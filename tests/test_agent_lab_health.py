from __future__ import annotations

from pathlib import Path

from agent_lab.cli import main
from agent_lab.events import load_events
from agent_lab.health import analyze_health_record, list_health_reports
from agent_lab.runtime import HarnessRuntime


def sample_health_text() -> str:
    return """年度体检报告

姓名：Demo User
血压 138/88 mmHg
空腹血糖 6.3 mmol/L
总胆固醇 5.9 mmol/L
低密度脂蛋白 LDL-C 3.8 mmol/L
高密度脂蛋白 HDL-C 1.2 mmol/L
甘油三酯 1.9 mmol/L
谷丙转氨酶 ALT 42 U/L

医生建议：注意饮食和运动，定期复查。
"""


def test_analyze_health_record_generates_safe_markdown(tmp_path: Path) -> None:
    source = tmp_path / "checkup.txt"
    output_dir = tmp_path / "health-output"
    events_path = tmp_path / "events.jsonl"
    source.write_text(sample_health_text(), encoding="utf-8")

    report = analyze_health_record(source, output_dir=output_dir, events_path=events_path)

    assert report.title == "年度体检报告"
    assert report.report_path == output_dir / "checkup.md"
    assert report.report_path.exists()
    assert report.indicators["血压"] == "138/88 mmHg"
    assert report.indicators["空腹血糖"] == "6.3 mmol/L"
    assert "低密度脂蛋白" in report.indicators
    assert "仅供健康信息整理与学习参考" in report.markdown
    assert "不能替代执业医师诊断、治疗或处方" in report.markdown
    assert "建议与医生沟通" in report.markdown
    assert "降压药" not in report.markdown

    events = load_events(events_path)
    assert [event.event_type for event in events] == [
        "health_record_analyzed",
        "health_report_generated",
    ]
    assert events[-1].payload["report_path"] == str(report.report_path)


def test_list_health_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "health-output"
    output_dir.mkdir()
    first = output_dir / "a.md"
    second = output_dir / "b.md"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")

    assert list_health_reports(output_dir) == [first, second]


def test_harness_runtime_runs_health_analysis(tmp_path: Path) -> None:
    source = tmp_path / "checkup.txt"
    output_dir = tmp_path / "health-output"
    events_path = tmp_path / "events.jsonl"
    source.write_text(sample_health_text(), encoding="utf-8")
    runtime = HarnessRuntime(events_path=events_path)

    result = runtime.run(
        "health.analyze",
        record_path=source,
        output_dir=output_dir,
    )

    assert result.action == "health.analyze"
    assert result.status == "completed"
    assert result.plan == [
        "Read health record text",
        "Extract common health indicators",
        "Write safety-bounded Markdown health summary",
        "Record health assistant events",
    ]
    assert "health-record-reading" in result.skills
    assert Path(result.artifacts["report_path"]).exists()
    assert result.events == ["health_record_analyzed", "health_report_generated"]


def test_cli_health_analyze_and_list(tmp_path: Path, capsys) -> None:
    source = tmp_path / "checkup.txt"
    output_dir = tmp_path / "health-output"
    events_path = tmp_path / "events.jsonl"
    source.write_text(sample_health_text(), encoding="utf-8")
    base_args = [
        "health",
        "--output-dir",
        str(output_dir),
        "--events-path",
        str(events_path),
    ]

    assert main([*base_args, "analyze", str(source)]) == 0
    generated = capsys.readouterr()
    assert "Generated health report" in generated.out
    assert "checkup.md" in generated.out

    assert main([*base_args, "list"]) == 0
    listed = capsys.readouterr()
    assert "checkup" in listed.out
