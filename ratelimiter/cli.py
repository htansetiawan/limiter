"""
Command Line Interface for Rate Limiter

Provides CLI commands for running rate limiter simulations and managing configurations.
"""

import click
import time
import random
import threading
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .algorithms import TokenBucket, LeakyBucket, SlidingWindow, FixedWindow, RateLimiter


console = Console()


class SimulationRunner:
    """Handles rate limiter simulation with real-time metrics"""

    def __init__(self, algorithm: str, rate: float, duration: int = 60,
                 request_rate: float = 10, burst_size: int = 5):
        self.algorithm = algorithm
        self.rate = rate
        self.duration = duration
        self.request_rate = request_rate  # requests per second to simulate
        self.burst_size = burst_size

        # Initialize rate limiter
        self.limiter = self._create_limiter(algorithm, rate)

        # Statistics
        self.total_requests = 0
        self.allowed_requests = 0
        self.denied_requests = 0
        self.start_time = None
        self.running = False

    def _create_limiter(self, algorithm: str, rate: float) -> RateLimiter:
        """Create rate limiter instance based on algorithm name"""
        algorithms = {
            'token_bucket': lambda: TokenBucket(rate, capacity=int(rate * 10)),
            'leaky_bucket': lambda: LeakyBucket(rate, capacity=int(rate * 5)),
            'sliding_window': lambda: SlidingWindow(rate, window_size=60.0),
            'fixed_window': lambda: FixedWindow(rate, window_size=60.0)
        }

        if algorithm not in algorithms:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        return algorithms[algorithm]()

    def simulate_request_burst(self, burst_size: int) -> tuple[int, int]:
        """Simulate a burst of requests"""
        allowed = 0
        denied = 0

        for _ in range(burst_size):
            if self.limiter.allow_request():
                allowed += 1
            else:
                denied += 1

        return allowed, denied

    def run_simulation(self) -> dict:
        """Run the simulation and return results"""
        self.start_time = time.time()
        self.running = True

        end_time = self.start_time + self.duration

        while time.time() < end_time and self.running:
            # Simulate varying request patterns
            if random.random() < 0.1:  # 10% chance of burst
                burst_size = random.randint(1, self.burst_size)
                allowed, denied = self.simulate_request_burst(burst_size)
            else:
                # Normal request pattern
                allowed, denied = self.simulate_request_burst(1)

            self.total_requests += (allowed + denied)
            self.allowed_requests += allowed
            self.denied_requests += denied

            # Sleep to simulate request rate
            time.sleep(1.0 / self.request_rate)

        self.running = False
        return self.get_results()

    def get_results(self) -> dict:
        """Get simulation results"""
        if not self.start_time:
            return {}

        duration = time.time() - self.start_time
        if duration == 0:
            duration = 0.001

        return {
            'total_requests': self.total_requests,
            'allowed_requests': self.allowed_requests,
            'denied_requests': self.denied_requests,
            'allow_rate': self.allowed_requests / self.total_requests if self.total_requests > 0 else 0,
            'actual_rate': self.allowed_requests / duration,
            'duration': duration,
            'algorithm': self.algorithm,
            'configured_rate': self.rate
        }

    def get_live_stats(self) -> dict:
        """Get current statistics for live display"""
        if not self.start_time:
            return {}

        current_time = time.time()
        duration = current_time - self.start_time

        return {
            'total_requests': self.total_requests,
            'allowed_requests': self.allowed_requests,
            'denied_requests': self.denied_requests,
            'allow_rate': self.allowed_requests / self.total_requests if self.total_requests > 0 else 0,
            'current_rate': self.allowed_requests / duration if duration > 0 else 0,
            'duration': duration,
            'limiter_stats': self.limiter.get_stats()
        }


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Rate Limiter CLI - Simulate and test rate limiting algorithms"""
    pass


@cli.command()
@click.option('--algorithm', '-a', type=click.Choice(['token_bucket', 'leaky_bucket', 'sliding_window', 'fixed_window']),
              default='token_bucket', help='Rate limiting algorithm to use')
@click.option('--rate', '-r', type=float, default=10.0, help='Rate limit (requests per second for Token/Leaky Bucket, requests per window for Sliding/Fixed Window)')
@click.option('--duration', '-d', type=int, default=60, help='Simulation duration in seconds')
@click.option('--request-rate', '--incoming-rate', '-rr', type=float, default=15.0, help='Simulated incoming request rate per second')
@click.option('--allowed-rate', '-ar', type=float, help='Alternative way to specify rate limit (same as --rate)')
@click.option('--burst-size', type=int, default=5, help='Maximum burst size for simulation')
@click.option('--live', is_flag=True, help='Show live statistics during simulation')
def start(algorithm, rate, duration, request_rate, allowed_rate, burst_size, live):
    """Start rate limiter simulation"""

    # Use allowed_rate if provided, otherwise use rate
    final_rate = allowed_rate if allowed_rate is not None else rate

    console.print(f"[bold green]Starting {algorithm.replace('_', ' ').title()} simulation...[/bold green]")
    console.print(f"Allowed Rate: {final_rate} req/s, Incoming Rate: {request_rate} req/s, Duration: {duration}s")

    runner = SimulationRunner(algorithm, final_rate, duration, request_rate, burst_size)

    if live:
        # Live simulation with real-time stats
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running simulation...", total=duration)

            # Start simulation in background thread
            result = None

            def run_sim():
                nonlocal result
                result = runner.run_simulation()

            sim_thread = threading.Thread(target=run_sim)
            sim_thread.start()

            # Display live stats
            start_time = time.time()
            while sim_thread.is_alive():
                current_time = time.time()
                elapsed = current_time - start_time

                if elapsed >= duration:
                    break

                stats = runner.get_live_stats()
                if stats:
                    progress.update(task, completed=int(elapsed))

                    # Create stats table
                    table = Table(title="Live Statistics")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="magenta")

                    table.add_row("Total Requests", str(stats['total_requests']))
                    table.add_row("Allowed", str(stats['allowed_requests']))
                    table.add_row("Denied", str(stats['denied_requests']))
                    table.add_row("Allow Rate", f"{stats['allow_rate']:.1%}")
                    table.add_row("Current Rate", f"{stats['current_rate']:.2f}")

                    console.print(table, end="\r")
                    time.sleep(0.5)

            sim_thread.join()
            progress.update(task, completed=duration)
    else:
        # Simple simulation without live display
        with console.status("[bold green]Running simulation...") as status:
            result = runner.run_simulation()

    # Display final results
    display_results(result)


@cli.command()
def list_algorithms():
    """List available rate limiting algorithms"""

    table = Table(title="Available Algorithms")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Description", style="white")

    algorithms = [
        ("token_bucket", "Allows bursts while maintaining average rate"),
        ("leaky_bucket", "Smooths requests at constant rate"),
        ("sliding_window", "Tracks requests in moving time window"),
        ("fixed_window", "Counts requests in fixed time intervals")
    ]

    for name, desc in algorithms:
        table.add_row(name.replace('_', ' ').title(), desc)

    console.print(table)


def display_results(result: dict):
    """Display simulation results in a formatted table"""

    if not result:
        console.print("[red]No results to display[/red]")
        return

    # Main results table
    table = Table(title="Simulation Results")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Algorithm", result['algorithm'].replace('_', ' ').title())
    table.add_row("Configured Rate", f"{result['configured_rate']:.1f}")
    table.add_row("Duration", f"{result['duration']:.1f}")
    table.add_row("Total Requests", str(result['total_requests']))
    table.add_row("Allowed Requests", str(result['allowed_requests']))
    table.add_row("Denied Requests", str(result['denied_requests']))
    table.add_row("Allow Rate", f"{result['allow_rate']:.1%}")
    table.add_row("Actual Rate", f"{result['actual_rate']:.2f}")

    console.print(table)

    # Performance analysis
    configured_rate = result['configured_rate']
    actual_rate = result['actual_rate']
    allow_rate = result['allow_rate']

    analysis = []
    if abs(actual_rate - configured_rate) / configured_rate < 0.1:
        analysis.append("[green]✓ Rate limit working as expected[/green]")
    else:
        analysis.append("[yellow]⚠ Rate limit deviation detected[/yellow]")

    if allow_rate > 0.95:
        analysis.append("[green]✓ High throughput maintained[/green]")
    elif allow_rate > 0.8:
        analysis.append("[yellow]⚠ Moderate throttling occurred[/yellow]")
    else:
        analysis.append("[red]✗ Heavy throttling detected[/red]")

    console.print("\n[bold]Analysis:[/bold]")
    for item in analysis:
        console.print(item)


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()
