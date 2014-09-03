import imagenet_psychophysics
conf_list = [('n13134947', 'n03001627'), ('n13134947', 'n04379243')]
URLs = imagenet_psychophysics.urls_from_confusion_list(conf_list, k=100, bucket_name='imagenet_test')
print URLs