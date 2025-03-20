#!/usr/bin/env python3

import asyncio
import docker
import argparse

async def push_image(image_name, username):
    """Asynchronously push a single image to Docker Hub"""
    # Process image name
    new_name = image_name.replace('__', '_s_')
    new_name = f"{username}/{new_name}"
    
    # Execute Docker commands via subprocess
    tag_cmd = f"docker tag {image_name} {new_name}"
    push_cmd = f"docker push {new_name}"
    
    # Tag the image
    proc = await asyncio.create_subprocess_shell(
        tag_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
    
    if proc.returncode != 0:
        return False
    
    # Push the image
    proc = await asyncio.create_subprocess_shell(
        push_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
    
    return proc.returncode == 0

async def process_with_semaphore(semaphore, image_name, username):
    """Use semaphore to control concurrency"""
    async with semaphore:
        return await push_image(image_name, username)

async def main():
    parser = argparse.ArgumentParser(description='Upload SWE-bench instance images to Docker Hub')
    parser.add_argument('--username', default='lycfight', help='Docker Hub username')
    parser.add_argument('--concurrent', type=int, default=32, help='Maximum concurrency')
    args = parser.parse_args()
    
    # Get all images
    client = docker.from_env()
    images = client.images.list()
    
    # Filter instance images
    instance_images = []
    for image in images:
        for tag in image.tags:
            if tag.startswith('sweb.eval.x86_64.'):
                instance_images.append(tag)
                
    if not instance_images:
        print("No instance images found")
        return
    
    print(f"Pushing {len(instance_images)} images...")
    
    # Create semaphore to control concurrency
    semaphore = asyncio.Semaphore(args.concurrent)
    
    # Asynchronously push all images using semaphore
    tasks = []
    for image_name in instance_images:
        task = asyncio.create_task(
            process_with_semaphore(semaphore, image_name, args.username)
        )
        tasks.append(task)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Count successful pushes
    success_count = sum(1 for r in results if r)
    print(f"Push completed: {success_count}/{len(instance_images)}")

if __name__ == "__main__":
    asyncio.run(main())