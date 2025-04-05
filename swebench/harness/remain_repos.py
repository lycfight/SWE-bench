import os
import json
from collections import defaultdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from datasets import Dataset

from swebench.harness.constants import KEY_INSTANCE_ID
from swebench.harness.utils import (
    get_predictions_from_file,
    str2bool,
)
from swebench.harness.run_validation import get_dataset_from_preds


def save_dataset_by_repo(dataset):
    """
    Save dataset grouped by repo to files
    
    Args:
        dataset: List of dataset instances
        
    Returns:
        dict: Dictionary of instances grouped by repo
    """
    # Group dataset by repo
    repo_groups = defaultdict(list)
    for instance in dataset:
        repo_groups[instance["repo"]].append(instance)
    
    # Create output directory
    output_dir = f"remain_repos"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save instances for each repo to a separate file
    for repo, instances in repo_groups.items():
        # Replace illegal characters in repo name to make it a valid filename
        output_file = os.path.join(output_dir, f"{repo.replace("/", "__")}.jsonl")
        
        # Convert list to Dataset and save as jsonl
        dataset_obj = Dataset.from_list(instances)
        dataset_obj.to_json(output_file, lines=True)
        
        print(f"Saved {len(instances)} instances to {output_file}")
    
    print(f"Total saved {len(repo_groups)} repositories")
    return repo_groups


def main(
    dataset_name: str,
    split: str,
    instance_ids: list,
    run_id: str,
    rewrite_reports: bool,
):
    # load predictions as map of instance_id to prediction
    gold_predictions = get_predictions_from_file("gold", dataset_name, split)
    gold_predictions = {pred[KEY_INSTANCE_ID]: pred for pred in gold_predictions}
    # get dataset from predictions
    dataset = get_dataset_from_preds(
        dataset_name, split, instance_ids, gold_predictions, run_id, rewrite_reports
    )
    
    # Save dataset grouped by repo
    repo_groups = save_dataset_by_repo(dataset)
    return

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Run remain repos harness for the given dataset and predictions.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    # Common args
    parser.add_argument(
        "--dataset_name",
        default="princeton-nlp/SWE-bench_Lite",
        type=str,
        help="Name of dataset or path to JSON file.",
    )
    parser.add_argument(
        "--split", type=str, default="test", help="Split of the dataset"
    )
    parser.add_argument(
        "--instance_ids",
        nargs="+",
        type=str,
        help="Instance IDs to run (space separated)",
    )
    parser.add_argument(
        "--run_id", type=str, required=True, help="Run ID - identifies the run"
    )

    parser.add_argument(
        "--rewrite_reports",
        type=str2bool,
        default=False,
        help="Doesn't run new instances, only writes reports for instances with existing test outputs",
    )
    
    args = parser.parse_args()
    main(**vars(args))
