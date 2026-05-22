import asyncio
from realestate_engine.scheduler.orchestrator import Orchestrator

async def test_scheduler():
    """Test scheduler initialization and job configuration."""
    print("=== Testing Scheduler ===")
    
    orchestrator = Orchestrator()
    
    # Check if silence period works
    is_silence = orchestrator._is_silence_period()
    print(f"Current silence period: {is_silence}")
    
    # Test scheduler start (without running forever)
    orchestrator.start()
    
    # Check jobs
    jobs = orchestrator.scheduler.get_jobs()
    print(f"\nScheduled jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job.name}: {job.trigger}")
    
    # Shutdown
    orchestrator.scheduler.shutdown()
    print("\n✅ Scheduler test completed")

if __name__ == "__main__":
    asyncio.run(test_scheduler())
