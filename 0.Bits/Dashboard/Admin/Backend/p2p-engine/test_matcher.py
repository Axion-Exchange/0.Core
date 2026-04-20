from src.logic.name_matcher import NameMatcher
import asyncio

async def test():
    matcher = NameMatcher()
    
    # Test 1: Forward subset
    print("Test 1: Forward subset")
    res1 = await matcher.match("JUAN CARLOS FLORES", "JUAN CARLOS FLORES FERRER")
    print(f"Matched: {res1.matched}")

    # Test 2: Reverse subset
    print("\nTest 2: Reverse subset")
    res2 = await matcher.match("FLORES FERRER JUAN CARLOS", "JUAN CARLOS FLORES")
    print(f"Matched: {res2.matched}")
    
    # What did fail?
    # What if payment had something extra?
    print("\nTest 3: Both have something the other doesn't")
    res3 = await matcher.match("FLORES FERRER JUAN CARLOS", "MR JUAN CARLOS FLORES")
    print(f"Matched: {res3.matched}")

if __name__ == "__main__":
    asyncio.run(test())
