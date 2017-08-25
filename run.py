import time
import boto.ec2
from frigga_snake.ami import AMIName
import sys


# provide these for the account you want to use
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""


if not len(sys.argv) > 1:
    print("Provide AWS Account numbers as args")
    exit(1)

conn_eu = boto.ec2.connect_to_region('eu-west-1', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
images = conn_eu.get_all_images(owners=sys.argv[1:])

groups = {}
images_with_missing_appversion = []

for image in images:
    if image.tags.get('appversion'):
        ami = AMIName(image.name, image.description, image.tags.get('appversion'))
        if ami.build_number:
            if ami.package_name not in groups:
                groups[ami.package_name] = []
            groups[ami.package_name].append(image)
    else:
        images_with_missing_appversion.append(image)

print ''
print ''

if len(images_with_missing_appversion):
    for img in images_with_missing_appversion:
        print img, img.name, img.description, img.tags
    print ''
    if raw_input('These images do not have an appversion. Do you want to delete them? Y/N: ').lower() == 'y':
        for img in images_with_missing_appversion:
            print 'deleting', img
            img.deregister(delete_snapshot=True)
            time.sleep(0.1)

print ''
print ''

for group, items in groups.items():
    print group, len(items)

print ''
if raw_input('Are you sure you want to delete all but the last 5 of these images? Y/N: ').lower() == 'y':
    for group, items in groups.items():
        try:
            print ''
            print '================='
            print 'GROUP:', group, len(items)
            print '================='
            sorted_items = sorted(items, key=lambda key: int(AMIName(key.name, key.description, key.tags['appversion']).build_number.replace("h", "")))
            for img in sorted_items[:-5]:
                print 'deleting', img
                img.deregister(delete_snapshot=True)
                time.sleep(0.1)
            print ''
        except Exception as e:
            print ''
            print '================='
            print 'EXCEPTION:'
            print '================='
            print e
            print ''
else:
    print 'Cancelled.'

print 'Done.'
