"""
CINT-70 Top Tier Benchmark Runner
Uses real NASA extracted data + experience memory
"""
import sys
import json
from datetime import datetime
from pathlib import Path
from src.agent.orchestrator import CINT70Orchestrator
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def load_extracted_data():
    """Load all real NASA-derived data files"""
    data = {}
    extracted = Path("data/extracted")
    
    files = {
        "thermal_constraints": "thermal_constraints.json",
        "sensor_specs": "sensor_specs.json",
        "environment_model": "environment_model.json",
        "joint_limits": "joint_limits.json",
        "obstacle_map": "obstacle_map.json",
        "tool_catalog": "tool_catalog.json",
        "failure_reports": "failure_reports.json",
        "task_library": "task_library.json",
        "safety_margins": "safety_margins.json",
    }
    
    for key, filename in files.items():
        filepath = extracted / filename
        if filepath.exists():
            with open(filepath) as f:
                data[key] = json.load(f)
            console.print(f"  ✅ Loaded {filename}")
        else:
            console.print(f"  ⚠️ Missing {filename}")
    
    return data

def run_full_benchmark():
    """Run complete CINT-70 benchmark with real data"""
    console.print("""
    ╔══════════════════════════════════════════════════╗
    ║     CINT-70 TOP TIER BENCHMARK SUITE             ║
    ║  NASA-Grounded Action-Execution Assurance         ║
    ╚══════════════════════════════════════════════════╝
    """, style="bold cyan")
    
    # Load real data
    console.print("\n[bold]Loading NASA Extracted Data...[/bold]")
    nasa_data = load_extracted_data()
    
    # Initialize orchestrator
    orchestrator = CINT70Orchestrator()
    
    # Load tasks from real task library
    tasks = nasa_data.get("task_library", {}).get("tasks", [])
    if not tasks:
        console.print("[red]No tasks found! Using fallback.[/red]")
        tasks = [
            {"task_id": "repair_001", "instruction": "Repair damaged thermal shield on panel 3"},
            {"task_id": "inspect_001", "instruction": "Inspect antenna array for damage"},
            {"task_id": "replace_001", "instruction": "Replace failed torque wrench"}
        ]
    
    # Failure modes
    failure_modes = [None, "stuck_joint", "camera_glare", "tool_failure", "signal_lag"]
    
    results = []
    
    for task in tasks:
        for failure in failure_modes:
            command = task["instruction"]
            task_id = task.get("task_id", "unknown")
            
            console.print(f"\n{'='*60}")
            console.print(f"[bold]Task: {task_id}[/bold]")
            if failure:
                console.print(f"[red]Chaos Mode: {failure}[/red]")
            console.print(f"{'='*60}")
            
            result = orchestrator.execute(command, inject_failure=failure)
            
            results.append({
                "task_id": task_id,
                "failure_mode": failure or "none",
                "approved": result.get("all_checks_passed", False),
                "trust_score": result.get("trust_score", 0),
                "recoveries": result.get("recovery_count", 0),
                "violations": len(result.get("violations", []))
            })
    
    # Compute metrics
    total = len(results)
    approved = sum(1 for r in results if r["approved"])
    rejected = total - approved
    aga = (approved / total) * 100 if total > 0 else 0
    
    # Average trust score
    avg_trust = sum(r["trust_score"] for r in results) / total if total > 0 else 0
    total_recoveries = sum(r["recoveries"] for r in results)
    total_violations = sum(r["violations"] for r in results)
    
    # Final Benchmark Report
    console.print("\n\n")
    console.print(Panel.fit(
        f"[bold]CINT-70 BENCHMARK RESULTS[/bold]\n\n"
        f"Total Tests: {total}\n"
        f"Approved: {approved}\n"
        f"Rejected: {rejected}\n"
        f"Action Grounding Accuracy (AGA): {aga:.1f}%\n"
        f"Average Trust Score: {avg_trust:.1%}\n"
        f"Total Recoveries: {total_recoveries}\n"
        f"Total Violations Detected: {total_violations}\n\n"
        f"Data Sources: NASA PDS MEDA, ISS Guides, LLIS, NASA Standards\n"
        f"Real Mars Readings: 3.2M temperature data points",
        title="FINAL BENCHMARK REPORT",
        border_style="cyan"
    ))
    
    # Per-task breakdown
    table = Table(title="Per-Task Results")
    table.add_column("Task", style="cyan")
    table.add_column("Failure", style="yellow")
    table.add_column("Result", style="bold")
    table.add_column("Trust", style="green")
    table.add_column("Recoveries", style="white")
    table.add_column("Violations", style="red")
    
    for r in results:
        status = "✅ APPROVED" if r["approved"] else "❌ REJECTED"
        style = "green" if r["approved"] else "red"
        table.add_row(
            r["task_id"],
            r["failure_mode"],
            f"[{style}]{status}[/{style}]",
            f"{r['trust_score']:.1%}",
            str(r["recoveries"]),
            str(r["violations"])
        )
    
    console.print(table)
    
    # Experience memory stats
    try:
        from src.memory.experience import ExperienceMemory
        mem = ExperienceMemory()
        stats = mem.get_stats()
        
        console.print(Panel.fit(
            f"[bold]EXPERIENCE MEMORY STATS[/bold]\n\n"
            f"Total Experiences Stored: {stats['total_experiences']}\n"
            f"Approved: {stats['approved']}\n"
            f"Rejected: {stats['rejected']}\n"
            f"Failure Patterns Learned: {stats['failure_patterns']}\n"
            f"Approval Rate: {stats['approval_rate']}\n\n"
            f"[italic]System learns from every run. Memory persists across sessions.[/italic]",
            title="LEARNING SYSTEM STATUS",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"  Memory stats unavailable: {e}")
    
    # Save results
    logs_dir = Path("logs/benchmarks")
    logs_dir.mkdir(parents=True, exist_ok=True)
    report_file = logs_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    benchmark_data = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": {
            "thermal": "NASA PDS Mars 2020 MEDA (3.2M readings)",
            "joints": "ISS Guide 2015 + CSA Canadarm2",
            "obstacles": "ISS Guide 2015 (digitized)",
            "tools": "NASA EVA Systems",
            "failures": "NASA LLIS (8 patterns)",
            "tasks": "ISS EVA + Mars 2020 Procedures",
            "safety": "NASA-SP-2016-6105 + NASA-STD-3001"
        },
        "results": results,
        "metrics": {
            "aga": aga,
            "avg_trust": avg_trust,
            "total_tests": total,
            "approved": approved,
            "rejected": rejected,
            "total_recoveries": total_recoveries,
            "total_violations": total_violations
        }
    }
    
    with open(report_file, "w") as f:
        json.dump(benchmark_data, f, indent=2)
    
    console.print(f"\n📁 Full report saved: {report_file}")
    
    return benchmark_data

if __name__ == "__main__":
    run_full_benchmark()