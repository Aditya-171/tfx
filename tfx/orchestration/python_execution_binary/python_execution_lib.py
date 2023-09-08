# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Library for executing Python executables."""
from typing import Union, cast

from absl import flags
from absl import logging
from tfx.dsl.io import fileio
from tfx.orchestration import metadata
from tfx.orchestration.portable import data_types
from tfx.orchestration.portable import python_driver_operator
from tfx.orchestration.python_execution_binary import python_execution_binary_utils
from tfx.proto.orchestration import driver_output_pb2
from tfx.proto.orchestration import executable_spec_pb2
from tfx.utils import import_utils

from tfx.orchestration.python_execution_binary import python_executor_operator_dispatcher

MLMD_CONNECTION_CONFIG_FLAG = flags.DEFINE_string(
    'tfx_mlmd_connection_config_b64', None,
    'wrapper proto containing MLMD connection config. If being set, this'
    'indicates a driver execution')


def _import_class_path(
    executable_spec: Union[executable_spec_pb2.PythonClassExecutableSpec,
                           executable_spec_pb2.BeamExecutableSpec],):
  """Import the class path from Python or Beam executor spec."""
  if isinstance(executable_spec, executable_spec_pb2.BeamExecutableSpec):
    beam_executor_spec = cast(executable_spec_pb2.BeamExecutableSpec,
                              executable_spec)
    import_utils.import_class_by_path(
        beam_executor_spec.python_executor_spec.class_path)
  else:
    python_class_executor_spec = cast(
        executable_spec_pb2.PythonClassExecutableSpec, executable_spec)
    import_utils.import_class_by_path(python_class_executor_spec.class_path)


def _run_driver(
    executable_spec: Union[executable_spec_pb2.PythonClassExecutableSpec,
                           executable_spec_pb2.BeamExecutableSpec],
    mlmd_connection_config: metadata.ConnectionConfigType,
    execution_info: data_types.ExecutionInfo) -> driver_output_pb2.DriverOutput:
  operator = python_driver_operator.PythonDriverOperator(
      executable_spec, metadata.Metadata(mlmd_connection_config))
  return operator.run_driver(execution_info)


def _run_python_custom_component(
    executable_spec: Union[
        executable_spec_pb2.PythonClassExecutableSpec,
        executable_spec_pb2.BeamExecutableSpec,
    ],
    execution_info: data_types.ExecutionInfo,
) -> None:
  """Run Python custom component declared with @component decorator."""
  # Eagerly import class path from executable spec such that all artifact
  # references are resolved.
  _import_class_path(executable_spec)

  # MLMD connection config being set indicates a driver execution instead of an
  # executor execution as accessing MLMD is not supported for executors.
  if MLMD_CONNECTION_CONFIG_FLAG.value:
    mlmd_connection_config = (
        python_execution_binary_utils.deserialize_mlmd_connection_config(
            MLMD_CONNECTION_CONFIG_FLAG.value))
    run_result = _run_driver(executable_spec,
                             mlmd_connection_config, execution_info)
  else:
    run_result = python_executor_operator_dispatcher.run_executor(
        executable_spec, execution_info
    )

  if run_result:
    with fileio.open(execution_info.execution_output_uri, 'wb') as f:
      f.write(run_result.SerializeToString())


def run(
    executable_spec: Union[
        executable_spec_pb2.PythonClassExecutableSpec,
        executable_spec_pb2.BeamExecutableSpec,
    ],
    execution_info: data_types.ExecutionInfo,
) -> None:
  """Run Python executable."""
  logging.info('Executing Python custom component')
  _run_python_custom_component(executable_spec, execution_info)
