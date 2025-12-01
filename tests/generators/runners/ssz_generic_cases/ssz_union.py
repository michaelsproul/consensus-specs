from random import Random

from eth2spec.debug.random_value import get_random_ssz_object, RandomizationMode
from eth2spec.utils.ssz.ssz_impl import serialize
from eth2spec.utils.ssz.ssz_typing import uint64, Union

from .ssz_test_case import invalid_test_case, invalid_test_case_unchecked, valid_test_case

# A simple Union type with None (selector 0) and uint64 (selector 1)
# This is the minimum type needed to test the Union decoding edge cases
UnionNoneUint64 = Union[None, uint64]


def valid_cases():
    rng = Random(1234)

    # None case (selector 0)
    yield (
        "none",
        valid_test_case(lambda: UnionNoneUint64(selector=0, value=None)),
    )

    # uint64 zero case (selector 1)
    yield (
        "uint64_zero",
        valid_test_case(lambda: UnionNoneUint64(selector=1, value=uint64(0))),
    )

    # uint64 max case (selector 1)
    yield (
        "uint64_max",
        valid_test_case(lambda: UnionNoneUint64(selector=1, value=uint64(2**64 - 1))),
    )

    # uint64 random cases
    for mode in [
        RandomizationMode.mode_zero,
        RandomizationMode.mode_max,
        RandomizationMode.mode_random,
    ]:
        for variation in range(3):
            yield (
                f"uint64_{mode.to_name()}_{variation}",
                valid_test_case(
                    lambda rng, mode=mode: UnionNoneUint64(
                        selector=1,
                        value=get_random_ssz_object(
                            rng,
                            uint64,
                            max_bytes_length=8,
                            max_list_length=1,
                            mode=mode,
                            chaos=False,
                        ),
                    ),
                    rng,
                ),
            )


def invalid_cases():
    # Empty data (no selector)
    yield (
        "no_selector",
        invalid_test_case(UnionNoneUint64, lambda: b""),
    )

    # None selector (0x00) with trailing bytes - THE KEY BUG CASE
    # This is the main test case for the issue - selector 0 (None) should have
    # no additional data, but buggy implementations may ignore trailing bytes.
    # Using invalid_test_case_unchecked because the Python SSZ implementation
    # does not currently detect this error (see https://github.com/ethereum/consensus-specs/issues/4763)
    yield (
        "none_with_one_trailing_byte",
        invalid_test_case_unchecked(lambda: b"\x00\x00"),
    )

    yield (
        "none_with_seven_trailing_bytes",
        invalid_test_case_unchecked(lambda: b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    )

    yield (
        "none_with_eight_trailing_bytes",
        invalid_test_case_unchecked(lambda: b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
    )

    yield (
        "none_with_nonzero_trailing_byte",
        invalid_test_case_unchecked(lambda: b"\x00\xff"),
    )

    # uint64 selector (0x01) with wrong length data
    yield (
        "uint64_selector_empty_data",
        invalid_test_case(UnionNoneUint64, lambda: b"\x01"),
    )

    yield (
        "uint64_selector_one_byte_short",
        invalid_test_case(UnionNoneUint64, lambda: b"\x01\x00\x00\x00\x00\x00\x00\x00"),
    )

    yield (
        "uint64_selector_one_byte_extra",
        invalid_test_case(UnionNoneUint64, lambda: b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
    )

    # Invalid selector values
    yield (
        "invalid_selector_2",
        invalid_test_case(UnionNoneUint64, lambda: b"\x02"),
    )

    yield (
        "invalid_selector_127",
        invalid_test_case(UnionNoneUint64, lambda: b"\x7f"),
    )

    yield (
        "invalid_selector_128",
        invalid_test_case(UnionNoneUint64, lambda: b"\x80"),
    )

    yield (
        "invalid_selector_255",
        invalid_test_case(UnionNoneUint64, lambda: b"\xff"),
    )

    # Invalid selector with valid-looking uint64 data
    yield (
        "invalid_selector_2_with_uint64_data",
        invalid_test_case(UnionNoneUint64, lambda: b"\x02" + serialize(uint64(123))),
    )
