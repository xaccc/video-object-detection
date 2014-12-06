'''
TODO
'''
from os.path import dirname, abspath, basename, join, exists
import sys
from PIL import Image
import numpy as np
from datetime import datetime

from video_id_fetcher import (get_noun_ids_and_video_ids,
                              get_egg_video_ids)
from video_fetcher import video_url, fetch_video
from image_utils import get_prepared_images
from classifier import classify
from detector import detect
from image_annotator import draw_detection_results
from image_utils import show_image

from config import TOP_PERCENTAGE

ROOT = dirname(abspath(__file__))

# The key is the trained model name, and the value is a tuple containing
# a path to the caffemodel and the deploy.prototxt of the trained model
MODELS = {
  # Accuracy per test iteration:
  #  0: 0.904
  #  2000: 0.976
  #  4000: 0.965
  #  6000: 0.965
  'alexnet': (
    '/Users/rose/home/video-object-detection/data/imagenet/n07840804/images/alexnet/snapshots/snapshot_iter_6000.caffemodel',
    '/Users/rose/home/video-object-detection/data/imagenet/n07840804/images/alexnet/aux/deploy.prototxt'
  ),
  # Accuracy per test iteration:
  #  0: 0.738
  #
  'nin-equal': (
    '/Users/rose/home/video-object-detection/data/imagenet/n07840804/images/nin-equal/snapshots/snapshot_iter_1000.caffemodel',
    '/Users/rose/home/video-object-detection/data/imagenet/n07840804/images/nin-equal/aux/deploy.prototxt'
  ),
}

def draw_noun_detections_on_video_frames(video_id, wnid):
  '''
  Draws boxes of detections of <wnid> on the frames of the video.
  The boxes have been non-maximally suppressed.

  Because selective search provides about 2000 boxes per frame, and the noun
  usually isn't even present, I don't consider a detection positive if the score
  for the positive class is higher than the negative class. Instead, I
  consider a detection positive if the positive score is > 0.99 (out of 1.00)

  If you want to change the drawing code, but not have to rerun the detection,
  simply delete the directory of annotated images you want to redraw (found in
  the data/imagenet/<wnid>/annotated directory)

  The names of the annotated directories take this form:
    <model>_<video_id>_<ms_betwen_frames>
  '''
  model = 'alexnet'
  ms_between_frames = 10000

  url = video_url(video_id)
  video_filename = fetch_video(url)
  image_dir = get_prepared_images(url, ms_between_frames, video_filename, wnid)
  wnid_dir = join(ROOT, 'data/imagenet', wnid)
  annotated_dir = join(wnid_dir, 'annotated', basename(image_dir))
  if exists(annotated_dir):
    return

  detections_filename = join('/tmp',
    '_'.join(['detection', 'results', model, wnid, video_id]) + '.bin')
  if not exists(detections_filename):
    detect(image_dir, detections_filename, MODELS[model][0], MODELS[model][1])
  if not exists(detections_filename):
    print 'Something went wrong during detection'
    sys.exit(1)
  draw_detection_results(detections_filename, annotated_dir)

def show_nouns_in_videos(num_videos_per_noun):
  '''
  Run tail -f /tmp/detector_log.txt to see progress.
  '''
  log_filename = '/tmp/detector_log.txt'
  with open(log_filename, 'a') as f:
    for noun_id, video_id_list in get_noun_ids_and_video_ids(
                        num_videos_per_noun).iteritems():
      for i, video_id in enumerate(video_id_list):
        draw_noun_detections_on_video_frames(video_id, noun_id)
        f.write(' '.join([str(datetime.now()),
                          noun_id,
                          video_id,
                          str(i) + '/' + str(num_videos_per_noun) + '\n',
                         ]))
        f.flush()

def test_classification(image_filename, wnid):
  '''
  Classifies one BGR image and shows the results
  '''
  # TODO this is out of date
  predictions = classify(image_filename)
  image = np.asarray(Image.open(
    draw_classifier_results(predictions, wnid, image_filename)))
  Image.fromarray(image).save(
    'data/labelled-test-images/' + basename(image_filename))
  show_image(image)

def test_classification_of_bananas():
  image_that_contains_bananas = '/Users/rose/video-object-detection/' + \
                                'data/images/9uddKYGPEkg_10000/30000.jpg'

  # the same image above, but cropped to contain only bananas
  image_that_contains_only_bananas = '/Users/rose/' + \
    'video-object-detection/data/test-images/bananas_only_30000.jpg'

  images = [image_that_contains_bananas,
            image_that_contains_only_bananas]

  for image in images:
    test_classification(image, 'banana')

def test_detector_on_eggs():
  video_ids = get_egg_video_ids(10)
  for video_id in video_ids:
    draw_noun_detections_on_video_frames(video_id, 'n07840804')

if __name__ == '__main__':
  test_detector_on_eggs()
