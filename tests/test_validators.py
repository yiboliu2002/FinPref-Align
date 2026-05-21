from finpref.data.validators import validate_dpo_row, validate_grpo_row, validate_sft_row


def test_validate_sft_row_passes_minimal_conversation():
    row = {
        "messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "a"},
        ]
    }
    assert validate_sft_row(row) == []


def test_validate_dpo_row_detects_missing_rejected():
    row = {"prompt": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], "chosen": [{"role": "assistant", "content": "a"}]}
    assert "missing rejected" in validate_dpo_row(row)


def test_validate_grpo_row_requires_meta():
    row = {"prompt": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]}
    assert "missing meta" in validate_grpo_row(row)

