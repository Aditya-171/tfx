# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""This module defines the entrypoint for the PythonExecutorOperator in TFX.

This library is intended to serve as the entrypoint for a binary that packages
the python executors in a pipeline. The resulting binary is called by the TFX
launcher and should not be called directly.
"""

from absl import flags
from absl import logging
from tfx.orchestration.python_execution_binary import python_execution_binary_utils
from tfx.orchestration.python_execution_binary import python_execution_lib

from google.protobuf import text_format

FLAGS = flags.FLAGS

EXECUTION_INVOCATION_FLAG = flags.DEFINE_string(
    'tfx_execution_info_b64', None, 'url safe base64 encoded binary '
    'tfx.orchestration.ExecutionInvocation proto')
EXECUTABLE_SPEC_FLAG = flags.DEFINE_string(
    'tfx_python_class_executable_spec_b64', None,
    'tfx.orchestration.executable_spec.PythonClassExecutableSpec proto')
BEAM_EXECUTABLE_SPEC_FLAG = flags.DEFINE_string(
    'tfx_beam_executable_spec_b64', None,
    'tfx.orchestration.executable_spec.BeamExecutableSpec proto')


def main(_):
  flags.mark_flag_as_required(EXECUTION_INVOCATION_FLAG.name)
  flags.mark_flags_as_mutual_exclusive(
      (EXECUTABLE_SPEC_FLAG.name, BEAM_EXECUTABLE_SPEC_FLAG.name),
      required=True)

  executable_spec = None
  if BEAM_EXECUTABLE_SPEC_FLAG.value is not None:
    executable_spec = python_execution_binary_utils.deserialize_executable_spec(
        BEAM_EXECUTABLE_SPEC_FLAG.value, with_beam=True
    )
  else:
    executable_spec = python_execution_binary_utils.deserialize_executable_spec(
        EXECUTABLE_SPEC_FLAG.value, with_beam=False
    )
  execution_info = python_execution_binary_utils.deserialize_execution_info(
      EXECUTION_INVOCATION_FLAG.value
  )
  logging.info('execution_info = %r\n', execution_info)
  logging.info(
      'executable_spec = %s\n', text_format.MessageToString(executable_spec)
  )

  python_execution_lib.run(executable_spec, execution_info)
