from diffusers import StableDiffusionXLImg2ImgPipeline
import argparse
import boto3
from botocore.config import Config
from PIL import Image
from io import BytesIO
import glob
import json
import os
import random
import torch

# 環境変数からパラメータを取得
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
arg_parser.add_argument('--s3-bucket', help='S3のバケットを指定します。')
arg_parser.add_argument('--s3-endpoint', help='S3互換エンドポイントのURLを指定します。')
arg_parser.add_argument('--s3-secret', help='S3のシークレットアクセスキーを指定します。')
arg_parser.add_argument('--s3-token', help='S3のアクセスキーIDを指定します。')

args = arg_parser.parse_args()

tasks = json.loads(args.prompt)
# S3クライアントの準備
s3_config = Config(
    # 互換性担保のため、設定を入れる。
    # https://cloud.sakura.ad.jp/news/2025/02/04/objectstorage_defectversion/?_gl=1%2Awg387d%2A_gcl_aw%2AR0NMLjE3NjgxMjIxMDEuQ2owS0NRaUFzWTNMQmhDd0FSSXNBRjZPNlhqR2V1aDdSejdHZkVUbS1SbTVKSkRBeE9CUGoxQ2FxUjlRQ3BSbFN5Vlo2M1h4UTlXVnVBa2FBdkxyRUFMd193Y0I.%2A_gcl_au%2ANzM1ODg0ODM0LjE3NjA5NjM5MDYuMTQzMDE2MzgwNS4xNzY4MDU2MzU3LjE3NjgwNjE2NTg.
    request_checksum_calculation="when_required",
    response_checksum_validation="when_required",
)

# キー情報を元にS3APIクライアントを作成
s3 = boto3.client(
    's3',
    endpoint_url=args.s3_endpoint if args.s3_endpoint else None,
    aws_access_key_id=args.s3_token,
    aws_secret_access_key=args.s3_secret,
    config=s3_config,
)

# CyberRealistic Ponyの動作準備
print('Start loading CyberRealistic Pony')
pipe = StableDiffusionXLImg2ImgPipeline.from_single_file(
    "/cyberrealisticpony/cyberrealisticPony_v150.safetensors",
    torch_dtype=torch.bfloat16,
    use_safetensors=True,
)

pipe.to('cuda')

print('Start editing images')
# 画像生成処理
for task in tasks:
    inputFileName, task_prompt, task_ng_prompt, suffix = task
    print(f'Current Task -> Input File: {inputFileName}, Prompt: {task_prompt}')

    # S3から入力画像をダウンロード
    response = s3.get_object(
        Bucket=args.s3_bucket,
        Key=inputFileName)
    init_image = Image.open(BytesIO(response["Body"].read())).convert("RGB").resize((int(args.width), int(args.height)), Image.LANCZOS)

    # seedを乱数生成
    current_seed = random.randint(0, 2**32 - 1)
    generator = torch.Generator(device="cuda").manual_seed(current_seed)

    # 出力命令
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

    #出力結果を出力フォルダに保存
    name, ext = os.path.splitext(inputFileName)
    images[0].save(
        os.path.join(
            args.output,
            '{}_{}.png'.format(name, suffix),
        ),
    )

# さくらのオブジェクトストレージに格納するための情報がある場合、S3互換APIでアップロード
if args.s3_token and args.s3_secret and args.s3_bucket:
    print('Start uploading to S3')

    # 出力フォルダ内のpngを順々に同名アップロード
    files = glob.glob(os.path.join(args.output, '*.png'))
    for file in files:
        print(os.path.basename(file))
 
        s3.upload_file(
            Filename=file,
            Bucket=args.s3_bucket,
            Key=os.path.basename(file),
            ExtraArgs={
                "ContentType": "image/png",
            },
        )