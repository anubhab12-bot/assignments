# Longest Consecutive Sequence
# Given an unsorted array of integers nums, return the length of the longest consecutive elements sequence.

# You must write an algorithm that runs in O(n) time.

# Example:

# js

# CopyEdit

# Input: [100, 4, 200, 1, 3, 2]

# Output: 4

# Explanation: The longest consecutive sequence is [1, 2, 3, 4].
# Expected: Use HashSet to achieve linear time complexity.


def longestConsecutive(nums):
    s = set(nums)
    longest_cons = 0

    for i in s:
        if i-1 not in s:
            curr = 1
            while i+1 in s:
                curr += 1
                i += 1
            longest_cons = max(longest_cons, curr) 
    return longest_cons

nums = [100, 4, 200, 1, 3, 2]
print(longestConsecutive(nums))