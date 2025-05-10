# Given an array nums of size n, return the majority element.
# The majority element is the element that appears more than ⌊n / 2⌋ times.
# You may assume that the majority element always exists in the array.

# Example:

# Input: [2,2,1,1,1,2,2]
# Output: 2

# Expected: Optimal solution in O(n) time using Boyer-Moore Voting Algorithm.



def majorityElement(nums):
    len_n = len(nums)
    count = 0
    elem = 0

    for i in range(len_n):
        if (count == 0):
            count += 1
            elem = nums[i]
        elif(nums[i] == elem):
            count += 1
        else:
            count -= 1
    return elem

   
nums = [2,2,1,1,1,2,2]
print(majorityElement(nums))