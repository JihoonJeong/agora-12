"""Crisis Seed 결정론 검증 스크립트
같은 seed로 CrisisSystem을 2번 돌렸을 때 동일한 위기 시퀀스가 나오는지 확인.
"""

from agora.core.crisis import CrisisSystem


def run_crisis_sequence(seed: int, epochs: int = 50) -> list[tuple[int, str]]:
    """주어진 seed로 crisis 시퀀스 생성"""
    cs = CrisisSystem(
        start_after_epoch=10,
        probability=0.3,
        extra_decay=5,
        duration=1,
        random_seed=seed,
    )
    events = []
    for epoch in range(1, epochs + 1):
        event = cs.check_and_trigger(epoch)
        if event:
            events.append((epoch, event.name))
    return events


def test_determinism():
    """같은 seed → 같은 시퀀스"""
    seed = 42
    seq1 = run_crisis_sequence(seed)
    seq2 = run_crisis_sequence(seed)

    print(f"Seed {seed} - Run 1: {seq1}")
    print(f"Seed {seed} - Run 2: {seq2}")

    assert seq1 == seq2, f"FAIL: 시퀀스 불일치!\n  Run1: {seq1}\n  Run2: {seq2}"
    print(f"PASS: 동일 seed({seed}) → 동일 위기 시퀀스 ({len(seq1)}건)")


def test_different_seeds():
    """다른 seed → 다른 시퀀스 (높은 확률)"""
    seq42 = run_crisis_sequence(42)
    seq99 = run_crisis_sequence(99)

    print(f"\nSeed 42: {seq42}")
    print(f"Seed 99: {seq99}")

    if seq42 != seq99:
        print("PASS: 다른 seed → 다른 위기 시퀀스")
    else:
        print("WARN: 다른 seed인데 우연히 동일 (가능은 하지만 매우 드묾)")


def test_persona_shuffle_determinism():
    """Persona 셔플도 seed로 결정론적인지 확인"""
    import random

    personas = [
        "influencer", "influencer", "archivist", "archivist",
        "merchant", "merchant", "jester", "jester",
        "citizen", "citizen", "observer", "architect",
    ]

    random.seed(42)
    p1 = personas.copy()
    random.shuffle(p1)

    random.seed(42)
    p2 = personas.copy()
    random.shuffle(p2)

    print(f"\nPersona shuffle (seed 42):")
    print(f"  Run 1: {p1}")
    print(f"  Run 2: {p2}")
    assert p1 == p2, "FAIL: Persona 셔플 불일치!"
    print("PASS: 동일 seed → 동일 persona 셔플")


def test_isolation():
    """Crisis RNG가 global random과 격리되어 있는지 확인"""
    import random

    # Global random을 다르게 소비해도 crisis 시퀀스는 동일해야 함
    seed = 42

    # Run 1: global random 0번 소비
    random.seed(999)
    seq1 = run_crisis_sequence(seed)

    # Run 2: global random 1000번 소비
    random.seed(999)
    for _ in range(1000):
        random.random()
    seq2 = run_crisis_sequence(seed)

    print(f"\nIsolation test:")
    print(f"  Global random 0회 소비 후: {seq1}")
    print(f"  Global random 1000회 소비 후: {seq2}")
    assert seq1 == seq2, "FAIL: Crisis RNG가 global random에 영향받음!"
    print("PASS: Crisis RNG는 global random과 완전 격리됨")


if __name__ == "__main__":
    test_determinism()
    test_different_seeds()
    test_persona_shuffle_determinism()
    test_isolation()
    print("\n=== 모든 테스트 통과 ===")
