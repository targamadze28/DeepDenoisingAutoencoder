import tensorflow as tf
import numpy as np
#import pdb


from model import REG
from preprocessing import Synth, GenMatrix
from os.path import join
from utils import search_wav
from sklearn.model_selection import train_test_split

np.random.seed(1234567)

FLAGS = tf.flags.FLAGS
tf.flags.DEFINE_string('clean_dir', r'C:\Users\Дмитрий\Desktop\qwr\DeepDenoisingAutoencoder\data\raw\clean',
                       'set clean data folder')
tf.flags.DEFINE_string('noise_dir', r'C:\Users\Дмитрий\Desktop\qwr\DeepDenoisingAutoencoder\data\raw\noise\audio',
                       'set noise data folder')
tf.flags.DEFINE_string('noisy_dir', r'..\data\noisy',
                       'set noisy(clean mixed with noise) data folder')
tf.flags.DEFINE_string('enhanced_dir', r'..\data\enhanced',
                       'set enhanced data folder')
tf.flags.DEFINE_string('training_files_dir', r'..\data\training_files',
                       'set training files folder')
tf.flags.DEFINE_string('tb_dir', r'..\model\tb_logs', 'save tensorboard logs')
tf.flags.DEFINE_string('saver_dir', r'..\model\saver', 'set folder for saver')
tf.flags.DEFINE_bool('TRAIN', True, 'train this model or not')
tf.flags.DEFINE_bool('TEST', True, 'test this model or not')
tf.flags.DEFINE_integer('n_cores', 20, 'set cpu cores')
tf.flags.DEFINE_integer('epochs', 10, 'epochs for training iterations')
tf.flags.DEFINE_integer('batch_size', 32, 'number of batch size')
tf.flags.DEFINE_float('learning_rate', 1e-3, 'learning rate')


def main():
    clean_dir = FLAGS.clean_dir
    noise_dir = FLAGS.noise_dir
    noisy_dir = FLAGS.noisy_dir
    enhanced_dir = FLAGS.enhanced_dir
    tb_dir = FLAGS.tb_dir
    saver_dir = FLAGS.saver_dir
    TRAIN = FLAGS.TRAIN
    TEST = FLAGS.TEST
    ncores = FLAGS.n_cores
    epochs = FLAGS.epochs
    batch_size = FLAGS.batch_size
    lr = FLAGS.learning_rate

    train_task = 'same_noise'  # set task name for noting your dataset

    # ===========================================================
    # ===========       Synthesize Noisy Data        ============
    # ===========================================================
    clean_file_list = search_wav(clean_dir)                                 
    clean_train_list, clean_test_list = train_test_split(
        clean_file_list, test_size=0.2)
    noise_file_list = search_wav(noise_dir)[0:20]
    noise_train_list, noise_test_list = train_test_split(
        noise_file_list, test_size=0.2)
    noise_test_list = noise_train_list # test on the same noise

    print('--- Synthesize Training Noisy Data ---')
    train_noisy_dir = join(noisy_dir, 'train')
    sr_clean = 16000
    sr_noise = 44100
    snr_list = ['20dB', '10dB', '0dB']
    data_num = None  # set data_num to make training data numbers for different snr
    syn_train = Synth(clean_train_list, noise_train_list, sr_clean, sr_noise)
    syn_train.gen_noisy(snr_list, train_noisy_dir,
                        data_num=data_num, ADD_CLEAN=True, cpu_cores=ncores)
    print('--- Synthesize Testing Noisy Data ---')
    test_noisy_dir = join(noisy_dir, 'test')
    sr_clean = 16000
    sr_noise = 44100
    data_num = None # set data_num to make testing data numbers for different snr
    snr_list = ['15dB']
    syn_test = Synth(clean_test_list, noise_test_list, sr_clean, sr_noise)
    syn_test.gen_noisy(snr_list, test_noisy_dir,
                        data_num=data_num, ADD_CLEAN=True, cpu_cores=ncores)
    # ===========================================================
    # ===========       Create Training Matrix       ============
    # ===========================================================
    print('--- Generate Training Matrix ---')
    train_task = 'same_noise'  # set task name for noting your dataset
    training_files_dir = FLAGS.training_files_dir
    train_noisy_dir = join(noisy_dir, 'train')
    DEL_TRAIN_WAV = True
    gen_mat = GenMatrix(training_files_dir, train_task, train_noisy_dir)
    split_num = 50  # number of spliting files
    iter_num = 2  # set iter number to use multi-processing, cpu_cores = split_num/iter_num
    input_sequence = False  # set input data is sequence or not
    gen_mat.create_h5(split_num=split_num, iter_num=iter_num,
                      input_sequence=input_sequence,
                      DEL_TRAIN_WAV=DEL_TRAIN_WAV)

    # ===========================================================
    # ===========             Main Model             ============
    # ===========================================================
    print('--- Build Model ---')
    note = 'DDAE'
    date = '0720'
    split_num = 50
    training_files_dir = FLAGS.training_files_dir
    model = REG(tb_dir, saver_dir, train_task, date, gpu_num='3', note=note)
    model.build(init_learning_rate=1e-3, reuse=False)

    print('--- Train Model ---')
    model.train(training_files_dir, split_num, epochs, batch_size)

    print('--- Test Model ---')
    testing_data_dir = join(noisy_dir, 'test')
    result_dir = '../data/enhanced/{}_{}/'.format(note, date)
    num_test = 30 # Set this number to decide how many testing data you wanna use. (None => All)
    cpu_cores = 30
    test_saver = '{}_{}/{}/best_saver_{}'.format(
        saver_dir, note, date, train_task)
    model.test(testing_data_dir, result_dir,
               test_saver, cpu_cores, num_test)


if __name__ == '__main__':
    main()
