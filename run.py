import time
import boto.ec2
from frigga_snake.ami import AMIName
import sys


NUMBER_OF_IMAGES_TO_KEEP = 10

# provide these for the account you want to use
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
ACCOUNT_ID = None


if not ACCOUNT_ID:
    if not len(sys.argv) > 1:
        print("Provide AWS Account ID as args")
        exit(1)
    ACCOUNT_ID = sys.argv[1:]

conn_eu = boto.ec2.connect_to_region('eu-west-1', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
images = conn_eu.get_all_images(owners=ACCOUNT_ID)

groups = {}
images_with_missing_appversion = []

for image in images:
    if image.tags.get('appversion'):
        ami = AMIName(image.name, image.description, image.tags.get('appversion'))
        if ami and hasattr(ami, 'build_number') and ami.build_number:
            if ami.package_name not in groups:
                groups[ami.package_name] = []
            groups[ami.package_name].append(image)
    else:
        images_with_missing_appversion.append(image)

print('')
print('')

if len(images_with_missing_appversion):
    for img in images_with_missing_appversion:
        print(img, img.name, img.description, img.tags)
    print('')
    if input('These images do not have an appversion. Do you want to delete them? Y/N: ').lower() == 'y':
        for img in images_with_missing_appversion:
            print('deleting', img)
            img.deregister(delete_snapshot=True)
            time.sleep(0.1)

print('')
print('')

for group, items in groups.items():
    if group != 'livestats':
        continue
    print('')
    print('=================')
    print('GROUP:', group, len(items))
    print('=================')
    sorted_items = sorted(items, key=lambda key: int(AMIName(key.name, key.description, key.tags['appversion']).build_number.replace("h", "")))
    for img in sorted_items:
        print(img, AMIName(img.name, img.description, img.tags['appversion']).build_number.replace("h", ""))
    print('')

print('')
if input('Are you sure you want to delete all but the last {} of these images? Y/N: '.format(NUMBER_OF_IMAGES_TO_KEEP)).lower() == 'y':
    for group, items in groups.items():
        if group != 'livestats':
            continue
        print('')
        print('=================')
        print('GROUP:', group, len(items))
        print('=================')
        sorted_items = sorted(items, key=lambda key: int(AMIName(key.name, key.description, key.tags['appversion']).build_number.replace("h", "")))
        for img in sorted_items[:-NUMBER_OF_IMAGES_TO_KEEP]:
            print('deleting', img, AMIName(img.name, img.description, img.tags['appversion']).build_number.replace("h", ""))
            try:
                img.deregister(delete_snapshot=True)
            except Exception as e:
                print('')
                print('=================')
                print('EXCEPTION:')
                print('=================')
                print(e)
                print('')
            time.sleep(0.1)
        print('')
else:
    print('Cancelled.')

print('Done.')
