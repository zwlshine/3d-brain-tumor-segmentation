import tensorflow as tf
from scipy.spatial.distance import directed_hausdorff

from utils.constants import *
from utils.utils import pred_to_one_hot


class HausdorffDistance(tf.keras.metrics.Mean):
    def __init__(self,
                 name='hausdorff_distance'):
        super(HausdorffDistance, self).__init__(name=name)

    def __call__(self, y_true, y_pred, sample_weight=None):
        return tf.reduce_max(directed_hausdorff(y_true, y_pred)[0], directed_hausdorff(y_pred, y_true)[0])


class DiceCoefficient(tf.keras.metrics.Mean):
    """Implements dice coefficient for binary classification."""
    def __init__(self,
                 name='dice_coefficient',
                 data_format='channels_last',
                 eps=1.0):
        super(DiceCoefficient, self).__init__(name=name)
        self.data_format = data_format
        self.eps = eps

    def __call__(self, y_true, y_pred, sample_weight=None):
        axis = (0, 1, 2, 3) if self.data_format == 'channels_last' else (0, 2, 3, 4)
        
        # Correct predictions will have 1, else 0.
        y_pred = tf.cast(y_pred > 0.5, tf.float32)
        intersection = tf.reduce_sum(y_pred * y_true, axis=axis)

        pred = tf.reduce_sum(y_pred, axis=axis)
        true = tf.reduce_sum(y_true, axis=axis)

        dice_coeff = tf.reduce_mean((2.0 * intersection + self.eps) / (pred + true + self.eps))

        return super(DiceCoefficient, self).update_state(
                            dice_coeff, sample_weight=sample_weight)


class GeneralizedDiceCoefficient(tf.keras.metrics.Mean):
    """Implements generalized dice coefficient for multiclass classification."""
    def __init__(self,
                 name='gen_dice_coefficient',
                 data_format='channels_last',
                 tumor_only=True,
                 eps=1.0):
        super(GeneralizedDiceCoefficient, self).__init__(name=name)
        self.data_format = data_format
        self.tumor_only = tumor_only
        self.eps = eps

    def update_state(self, y_true, y_pred, sample_weight=None):
        y_pred = pred_to_one_hot(y_pred, self.data_format)

        # Correct predictions will have 1, else 0.
        intersection = y_pred * y_true

        # Sum up matches per channel.
        axis = (0, 1, 2, 3) if self.data_format == 'channels_last' else (0, 2, 3, 4)
        intersection = tf.reduce_sum(intersection, axis=axis)

        # Count total number of each label.
        true_voxels = tf.reduce_sum(y_true, axis=axis)
        pred_voxels = tf.reduce_sum(y_pred, axis=axis)

        # Dice coefficients per channel.
        dice_coeff = (2.0 * intersection + self.eps) / (true_voxels + pred_voxels + self.eps)
        if self.tumor_only:
            dice_coeff = tf.reduce_mean(dice_coeff[1:])
        else:
            dice_coeff = tf.reduce_mean(dice_coeff)

        return super(GeneralizedDiceCoefficient, self).update_state(
                            dice_coeff, sample_weight=sample_weight)
