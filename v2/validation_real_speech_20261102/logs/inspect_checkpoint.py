import sys
from pathlib import Path
sys.path.insert(0,str(Path('03_过程与分析/05_工具/tf24_env/Lib/site-packages').resolve()))
import tensorflow as tf
from tensorflow.core.protobuf import trackable_object_graph_pb2
r=tf.train.load_checkpoint('01_核心参考/keyword-transformer-master/models_data_v2_12_labels/kwt1/best_weights')
g=trackable_object_graph_pb2.TrackableObjectGraph();g.ParseFromString(r.get_tensor('_CHECKPOINTABLE_OBJECT_GRAPH'))
for node in g.nodes:
 for a in node.attributes:
  if a.name=='VARIABLE_VALUE' and 'optimizer' not in a.checkpoint_key:
   print(a.full_name, a.checkpoint_key, r.get_tensor(a.checkpoint_key).shape)
