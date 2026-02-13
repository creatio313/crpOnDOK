import runner_util
import argparse
from diffusers import StableDiffusionXLImg2ImgPipeline
from io import BytesIO
import json
import logging
from PIL import Image
from pathlib import Path
import random
import sys
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    '--output',
    default='/opt/artifact',
    help='出力先ディレクトリを指定します。',
)
arg_parser.add_argument(
    '--prompt', 
    default='[["img.jpg", "score_9, score_8_up, score_7_up, An astronaut riding a green horse","score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs", "edited"]]', 
    help='[["filename", "prompt","ng_prompt","suffix"], ...] 形式のJSON文字列を指定します。'
)
arg_parser.add_argument(
    '--steps',
    type=int,
    default=20,
    help='サンプリングステップ数を指定します。',
)
arg_parser.add_argument(
    '--strength',
    type=float,
    default=0.75,
    help='画像の変化の強さを指定します。',
)
arg_parser.add_argument(
    '--width',
    type=int,
    default=896,
    help='出力画像の幅を指定します。',
)
arg_parser.add_argument(
    '--height',
    type=int,
    default=1152,
    help='出力画像の高さを指定します。',
)
arg_parser.add_argument('--objst-input-bucket', help='オブジェクトストレージのバケットを指定します。')
arg_parser.add_argument('--objst-output-bucket', help='オブジェクトストレージのバケットを指定します。')
arg_parser.add_argument('--objst-endpoint', help='S3互換エンドポイントのURLを指定します。')
arg_parser.add_argument('--objst-secret', help='オブジェクトストレージのシークレットアクセスキーを指定します。')
arg_parser.add_argument('--objst-token', help='オブジェクトストレージのアクセスキーIDを指定します。')
args = arg_parser.parse_args()

# S3互換APIクライアントの生成
if args.objst_token and args.objst_secret and args.objst_endpoint:
    object_storage_client = runner_util.genObjectStorageClient(endpoint=args.objst_endpoint,
                            token=args.objst_token,
                            secret=args.objst_secret)
else:
    logging.error('S3互換APIクライアントの情報が不足しています。処理を中断します。')
    sys.exit(1)

# CyberRealistic Ponyの動作準備
logging.info('CyberRealistic Ponyを読み込みます。')
pipe = StableDiffusionXLImg2ImgPipeline.from_single_file(
    "/cyberrealisticpony/cyberrealisticPony_v150.safetensors",
    torch_dtype=torch.bfloat16,
    use_safetensors=True,
).to('cuda')
logging.info('CyberRealistic Ponyを読み込みました。')

logging.info('主処理開始')
tasks = json.loads(args.prompt)
for task in tasks:
    # タスク情報を取得し、ファイルパス・プロンプトが存在しない場合はスキップ
    input_file_path, task_prompt, task_ng_prompt, suffix = task
    if not input_file_path or not task_prompt or not task_ng_prompt:
        logging.warning(f'必須パラメータが不足しているため、処理をスキップしました。: {task}')
        continue

    logging.info(f'画像編集タスク開始 -> ファイルパス: {input_file_path}, プロンプト: {task_prompt}, 接尾辞: {suffix}')

    # オブジェクトストレージから入力画像をダウンロード
    try:
        logging.info(f'入力画像を取得します。バケット: {args.objst_input_bucket}, ファイルパス: {input_file_path}')
        response = object_storage_client.get_object(
            Bucket=args.objst_input_bucket,
            Key=input_file_path)
        image_data = response["Body"].read()
        init_image = Image.open(BytesIO(image_data)).convert("RGB").resize((int(args.width), int(args.height)), Image.LANCZOS)
        response["Body"].close()
    except Exception as e:
        logging.error(f'入力画像の取得に失敗しました。: {e}')
        continue
    else:
        logging.info('入力画像の取得に成功しました。')

    # seedを乱数生成
    generator = torch.Generator(device="cuda").manual_seed(random.getrandbits(32))

    logging.info('画像編集を実行します。')
    # 出力命令。guidance_scaleは推奨値に固定しているが、変更も可能。
    images = pipe(
        prompt=task_prompt,
        negative_prompt=task_ng_prompt,
        image=init_image,
        generator=generator,
        strength=(args.strength),
        height=int(args.height),
        num_inference_steps=int(args.steps),
        guidance_scale=8,
        output_type='pil',
        width=int(args.width),
    ).images
    logging.info('画像編集が完了しました。')

    #出力結果を出力フォルダに保存
    output_path = runner_util.genOutputPath(input_file_path, suffix)
    local_output_path = Path(args.output) / output_path

    logging.info(f'画像をローカルに保存します。パス: {local_output_path}')
    runner_util.saveImageLocally(images[0], local_output_path)
    logging.info('画像をローカルに保存しました。')

    # オブジェクトストレージにアップロード
    logging.info(f'画像をオブジェクトストレージにアップロードします。バケット: {args.objst_output_bucket}, ファイルパス: {output_path}')
    object_storage_client.upload_file(
        Filename=str(local_output_path),
        Bucket=args.objst_output_bucket,
        Key=output_path,
        ExtraArgs={
            "ContentType": "image/png",
        },
    )
    logging.info(f'画像をオブジェクトストレージにアップロードしました。バケット: {args.objst_output_bucket}, ファイルパス: {output_path}')

logging.info('主処理終了')