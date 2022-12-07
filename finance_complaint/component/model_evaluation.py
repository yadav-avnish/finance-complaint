from finance_complaint.entity.artifact_entity import (ModelEvaluationArtifact, DataValidationArtifact,
    ModelTrainerArtifact)
from finance_complaint.entity.config_entity import ModelEvaluationConfig
from finance_complaint.entity.schema import FinanceDataSchema
from finance_complaint.exception import FinanceException
from finance_complaint.logger import logger
import sys
from pyspark.sql import DataFrame
from pyspark.ml.feature import StringIndexerModel
from pyspark.ml.pipeline import PipelineModel
from finance_complaint.config.spark_manager import spark_session
from finance_complaint.utils import get_score

from pyspark.sql.types import StringType, FloatType, StructType, StructField
from finance_complaint.data_access.model_eval_artifact import ModelEvaluationArtifactData
from finance_complaint.ml.estimator import  ModelResolver,FinanceComplaintEstimator

class ModelEvaluation:

    def __init__(self,
                 data_validation_artifact: DataValidationArtifact,
                 model_trainer_artifact: ModelTrainerArtifact,
                 model_eval_config: ModelEvaluationConfig,
                 schema=FinanceDataSchema()
                 ):
        try:
            self.model_eval_artifact_data = ModelEvaluationArtifactData()
            self.data_validation_artifact = data_validation_artifact
            self.model_eval_config = model_eval_config
            self.model_trainer_artifact = model_trainer_artifact
            self.schema = schema
            self.model_resolver = ModelResolver()

            self.finance_estimator = FinanceComplaintEstimator()

        except Exception as e:
            raise FinanceException(e, sys)


    def read_data(self) -> DataFrame:
        try:
            file_path = self.data_validation_artifact.accepted_file_path
            dataframe: DataFrame = spark_session.read.parquet(file_path)
            return dataframe
        except Exception as e:
            # Raising an exception.
            raise FinanceException(e, sys)

    def evaluate_trained_model(self) -> ModelEvaluationArtifact:
        try:
            if not self.model_resolver.is_model_present:

                model_evaluation_artifact = ModelEvaluationArtifact(
                    model_accepted=True,
                    changed_accuracy= None,
                    trained_model_path = self.model_trainer_artifact.model_trainer_ref_artifact.trained_model_file_path,
                    best_model_path = None,
                    active=True
                )
                return  model_evaluation_artifact

            #set initial flag
            is_model_accepted, is_active = False, False

            #obtain required directory path
            trained_model_file_path = self.model_trainer_artifact.model_trainer_ref_artifact.trained_model_file_path
            label_indexer_model_path = self.model_trainer_artifact.model_trainer_ref_artifact.label_indexer_model_file_path

            #load required model and label index
            label_indexer_model = StringIndexerModel.load(label_indexer_model_path)
            trained_model = PipelineModel.load(trained_model_file_path)

            #Read the dataframe
            dataframe: DataFrame = self.read_data()
            #transform the target column
            dataframe = label_indexer_model.transform(dataframe)

            best_model_path = self.finance_estimator.get_latest_model_path()

            #prediction using trained model
            trained_model_dataframe = trained_model.transform(dataframe)
            #prediction using best model
            best_model_dataframe = self.finance_estimator.transform(dataframe)

            #compute f1 score for trained model
            trained_model_f1_score = get_score(dataframe=trained_model_dataframe, metric_name="f1",
                                            label_col=self.schema.target_indexed_label,
                                            prediction_col=self.schema.prediction_column_name)
            #compute f1 score for best model
            best_model_f1_score = get_score(dataframe=best_model_dataframe, metric_name="f1",
                                            label_col=self.schema.target_indexed_label,
                                            prediction_col=self.schema.prediction_column_name)

            logger.info(f"Trained_model_f1_score: {trained_model_f1_score}, Best model f1 score: {best_model_f1_score}")
            #improved accuracy
            changed_accuracy = trained_model_f1_score - best_model_f1_score

            if changed_accuracy >= self.model_eval_config.threshold:
                is_model_accepted, is_active = True, True

            model_evaluation_artifact = ModelEvaluationArtifact(model_accepted=is_model_accepted,
                                                                changed_accuracy=changed_accuracy,
                                                                trained_model_path=trained_model_file_path,
                                                                best_model_path=best_model_path,
                                                                active=is_active
                                                                )
            return model_evaluation_artifact
        except Exception as e:
            raise FinanceException(e,sys)

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        try:
            model_accepted = True
            is_active = True
            model_evaluation_artifact = self.evaluate_trained_model()
            logger.info(f"Model evaluation artifact: {model_evaluation_artifact}")
            self.model_eval_artifact_data.save_eval_artifact(model_eval_artifact=model_evaluation_artifact)
            return model_evaluation_artifact
        except Exception as e:
            raise FinanceException(e, sys)
