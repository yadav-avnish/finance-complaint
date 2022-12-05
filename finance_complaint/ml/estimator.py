import sys

from finance_complaint.exception import FinanceException
from pyspark.ml.pipeline import PipelineModel
from pyspark.sql import DataFrame

import shutil
import os
from finance_complaint.constant.model import MODEL_SAVED_DIR
import time
from typing import List, Optional
import re
from abc import abstractmethod, ABC
from finance_complaint.config.aws_connection_config import AWSConnectionConfig


class FinanceComplaintEstimator:

    def __init__(self, **kwargs):
        try:
            if len(kwargs) > 0:
                super().__init__(**kwargs)

            self.model_dir = MODEL_SAVED_DIR
            self.loaded_model_path = None
            self.__loaded_model = None
        except Exception as e:
            raise FinanceException(e, sys)

    def get_model(self) -> PipelineModel:
        try:
            latest_model_path = self.get_latest_model_path()
            if latest_model_path != self.loaded_model_path:
                self.__loaded_model = PipelineModel.load(latest_model_path)
                self.loaded_model_path = latest_model_path
            return self.__loaded_model
        except Exception as e:
            raise FinanceException(e, sys)

    def get_latest_model_path(self, ):
        try:
            dir_list = os.listdir(self.model_dir)
            latest_model_folder = dir_list[-1]
            tmp_dir = os.path.join(self.model_dir, latest_model_folder)
            model_path = os.path.join(self.model_dir, latest_model_folder, os.listdir(tmp_dir)[-1])
            return model_path
        except Exception as e:
            raise FinanceException(e, sys)

    def transform(self, dataframe) -> DataFrame:
        try:
            model = self.get_model()
            return model.transform(dataframe)
        except Exception as e:
            raise FinanceException(e, sys)

