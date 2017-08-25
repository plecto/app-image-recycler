import time
import boto.ec2
from frigga_snake.ami import AMIName
import sys

if not len(sys.argv) > 1:
    print("Provide AWS Account numbers as args")
    exit(1)

conn_eu = boto.ec2.connect_to_region('eu-west-1')
images = conn_eu.get_all_images(owners=sys.argv[1:])

groups = {}

for image in images:
    try:
        ami = AMIName(image.name, image.description, image.tags.get('appversion'))
        if ami.build_number:
            if ami.package_name not in groups:
                groups[ami.package_name] = []
            groups[ami.package_name].append(image)
    except TypeError:
        print image.name, image.description, image.tags

for group, items in groups.items():
    try:
        print group, len(items)
        sorted_items = sorted(items, key=lambda key: int(AMIName(key.name, key.description, key.tags['appversion']).build_number.replace("h", "")))
        for img in sorted_items[:-2]:
            img.deregister(delete_snapshot=True)
            time.sleep(0.1)
    except Exception as e:
        print e
