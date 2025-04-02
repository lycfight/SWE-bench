import docker
import requests
from argparse import ArgumentParser
import json

from swebench.harness.constants import KEY_INSTANCE_ID
from swebench.harness.utils import load_swebench_dataset, str2bool, run_threadpool


def check_local_image(instance, instance_image_tag):
    """Check if image exists locally
    
    Args:
        instance (dict): Instance data containing instance_id
        instance_image_tag (str): Image tag
        
    Returns:
        tuple: (exists, image_name)
    """
    client = docker.from_env()
    instance_id = instance[KEY_INSTANCE_ID]
    image_name = f"sweb.eval.x86_64.{instance_id.lower()}:{instance_image_tag}"
    
    try:
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False


def push_image(instance, namespace, instance_image_tag):
    """Push an image to Docker Hub
    
    Args:
        instance (dict): Instance data containing instance_id
        namespace (str): Docker Hub namespace
        instance_image_tag (str): Image tag
        
    Returns:
        dict: Result containing status and instance_id
    """
    client = docker.from_env()
    instance_id = instance[KEY_INSTANCE_ID]
    
    image_name = f"sweb.eval.x86_64.{instance_id.lower()}:{instance_image_tag}"
    new_image_name = f"{namespace}/{image_name}".replace("__", "_s_")
    
    # Get and tag the image
    image = client.images.get(image_name)
    image.tag(new_image_name)
    
    # Push the image
    for line in client.images.push(new_image_name, stream=True, decode=True):
        if 'error' in line:
            raise Exception(line['error'])
    
    # Remove the image from local
    client.images.remove(new_image_name, force=True)
    client.images.remove(image_name, force=True)
    
    return


def main(
    dataset_name,
    split,
    max_workers,
    namespace,
    instance_image_tag,
):
    """Push Docker images for the specified dataset
    
    Args:
        dataset_name (str): Name of the dataset to use
        split (str): Dataset split to use
        max_workers (int): Number of workers for parallel processing
        namespace (str): Docker Hub namespace
        instance_image_tag (str): Tag to use for the images
    """
    # Load dataset
    dataset = load_swebench_dataset(dataset_name, split)
    total_instances = len(dataset)
    print(f"Found {total_instances} total instances")

    # First phase: Check local images
    to_push = []
    for instance in dataset:
        exists = check_local_image(instance, instance_image_tag)
        if exists:
            to_push.append(instance)
    print(f"Found {len(to_push)} images to push")
    
    if not to_push:
        print("No local images found to push")
        return

    # 记录所有成功的实例
    all_successful = []
    current_batch = to_push
    retry_count = 0

    while current_batch:
        retry_count += 1
        print(f"\nAttempt #{retry_count}")
        print(f"Pushing {len(current_batch)} images to Docker Hub...")
        
        # 准备推送任务
        push_payloads = [
            (instance, namespace, instance_image_tag)
            for instance in current_batch
        ]
        
        # 执行推送
        successful, failed = run_threadpool(push_image, push_payloads, max_workers)
        
        # 更新统计信息
        all_successful.extend(successful)
        current_batch = [payload[0] for payload in failed]  # 获取失败的实例用于下一轮重试
        
        # 打印当前轮次结果
        print(f"\nPush results for attempt #{retry_count}:")
        print(f"- Successfully pushed in this attempt: {len(successful)}")
        print(f"- Failed in this attempt: {len(failed)}")
        print(f"- Total successful so far: {len(all_successful)}")
        print(f"- Remaining to push: {len(current_batch)}")
        
        if current_batch:
            print("\nRetrying failed instances...")
        else:
            print("\nAll images have been successfully pushed!")
    
    return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="princeton-nlp/SWE-bench_Lite",
        help="Name of the dataset to use",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Split to use"
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="Max workers for parallel processing"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="lycfight",
        help="Docker Hub namespace"
    )
    parser.add_argument(
        "--instance_image_tag",
        type=str,
        default="latest",
        help="Tag to use for the images"
    )
    args = parser.parse_args()
    main(**vars(args))