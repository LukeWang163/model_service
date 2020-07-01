import tensorflow as tf
from tf import log
from tensorflow.python.tools import saved_model_cli

LOGGER = log.getLogger(__name__)


class ModelDef:

    def __init__(self, model_name, model_path):
        self.model_name = model_name
        self.model_path = model_path
        self.model_outputs = {}
        self.model_inputs = {}

        signature_def_map = saved_model_cli.get_signature_def_map(model_path, tf.saved_model.tag_constants.SERVING)

        signature = []
        # only one allowed
        for name in signature_def_map:
            signature.append(name)
            LOGGER.info("signature name: %s", name)
        if len(signature) == 1:
            self.model_signature = signature[0]
        else:
            self.model_signature = tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY
            LOGGER.warning("signatures more than one, use serving_default signature")

        LOGGER.info("model signature: %s", self.model_signature)

        for i in signature_def_map[self.model_signature].inputs:
            tensorinfo = signature_def_map[self.model_signature].inputs[i]
            input_name = tensorinfo.name
            dtype_constant = tensorinfo.dtype

            input_dtype = tf.as_dtype(dtype_constant)

            self.model_inputs[i] = input_dtype

        LOGGER.info("model inputs: %s", self.model_inputs)

        for i in signature_def_map[self.model_signature].outputs:
            tensorinfo = signature_def_map[self.model_signature].outputs[i]
            output_name = tensorinfo.name
            dtype_constant = tensorinfo.dtype

            output_dtype = tf.as_dtype(dtype_constant)

            self.model_outputs[i] = output_dtype

        LOGGER.info("model outputs: %s", self.model_outputs)
