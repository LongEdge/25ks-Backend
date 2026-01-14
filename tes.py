from typing import List


def majorityElement(nums: List[int]) -> int:
    count = 0
    num = -1
    # for i in nums[:len(nums) - 2]:
    for i in range(len(nums)):
        if num == -1:
            num = nums[i]
            count = 1
            continue
        if count == 0:
            num = nums[i]
            count = 1
            continue
        if  i != len(nums)-1 and num == nums[i ]:
            count += 1
        if i != len(nums)-1 and num != nums[i ] :
            count -= 1
    return num

nums=[3,3,4]
print(majorityElement(nums))