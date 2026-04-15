import numpy as np
import random as random

class EndfieldGacha:
    #gacha constants
    BASE_RATE_6 = 0.008
    SOFT_PITY_START = 65
    SOFT_PITY_RAMP = 0.05
    GUARANTEE = 120
    FREETOKEN = 240
    RATEUPRATE = 0.5

    #precompute prob table to avoid costly branches in loops
    prob_table = []
    for _i in range(80):
        if _i <= SOFT_PITY_START:
            prob_table.append(BASE_RATE_6)
        else:
            prob_table.append(max(BASE_RATE_6 + (_i - SOFT_PITY_START) * SOFT_PITY_RAMP, _i == 79))
    
    prob_table = np.array(prob_table)

    def __init__(self,Nsims,StartingSixStarDropPity = 0, RateUpAcquiredFromStart = False, StartingPulls = 0):

        self.Nsims = Nsims
        self.StartingSixStarDropPity = StartingSixStarDropPity
        self.SixStarDropPity = self.StartingSixStarDropPity*np.ones(Nsims, dtype = int)
        self.RateUpCopiesCount = np.zeros(Nsims, dtype = int)
        self.OffBanner6StarCount = np.zeros(Nsims, dtype = int)
        self.PullsTowardsGuarantee = np.zeros(Nsims, dtype = int)
        self.RateUpAcquiredFromStart = RateUpAcquiredFromStart
        self.RateUpAcquired = self.RateUpAcquiredFromStart*np.ones(Nsims, dtype = int)
        self.StartingPulls = StartingPulls
        self.TotalPulls = self.StartingPulls*np.ones(Nsims, dtype = int)

        

    def Pull(self):
        self.SixStarDropPity += 1
        self.TotalPulls += 1
        self.PullsTowardsGuarantee += 1
        self.PullsTowardsGuarantee *= (self.RateUpAcquired == 0)
        
        self.RateUpCopiesCount += self.TotalPulls%self.FREETOKEN == 0

        # --- Check 2: Roll for 6-Star ---
        prob_6 = self.prob_table[np.minimum(self.SixStarDropPity - 1,79)]

        Pull = np.random.rand(self.Nsims,1)
        RateUpGet = (Pull <= prob_6*EndfieldGacha.RATEUPRATE) | (self.PullsTowardsGuarantee == EndfieldGacha.GUARANTEE)
        self.RateUpCopiesCount += RateUpGet
        self.RateUpAcquired += RateUpGet

        OffRateGet = (Pull >= (1-prob_6*(1-EndfieldGacha.RATEUPRATE))) & (self.PullsTowardsGuarantee != EndfieldGacha.GUARANTEE)
        self.OffBanner6StarCount += OffRateGet

        self.SixStarDropPity *= ((RateUpGet | OffRateGet) == 0)


    def PullSelected(self, Indices):
        PullsToDo = len(Indices)
        self.SixStarDropPity[Indices] += 1
        self.TotalPulls[Indices] += 1
        self.PullsTowardsGuarantee[Indices] += 1
        self.PullsTowardsGuarantee[Indices] *= (self.RateUpAcquired[Indices] == 0)
        
        self.RateUpCopiesCount[Indices] += self.TotalPulls[Indices]%self.FREETOKEN == 0

        # --- Check 2: Roll for 6-Star ---
        prob_6 = self.prob_table[np.minimum(self.SixStarDropPity[Indices] - 1,79)]

        Pull = np.random.rand(PullsToDo,1)
        RateUpGet = (Pull <= prob_6*self.RATEUPRATE) | (self.PullsTowardsGuarantee[Indices] == self.GUARANTEE)
        self.RateUpCopiesCount[Indices] += RateUpGet
        self.RateUpAcquired[Indices] += RateUpGet

        OffRateGet = (Pull >= (1-prob_6*(1-self.RATEUPRATE))) & (self.PullsTowardsGuarantee[Indices] != self.GUARANTEE)
        self.OffBanner6StarCount[Indices] += OffRateGet

        self.SixStarDropPity[Indices] *= ((RateUpGet | OffRateGet) == 0)
        
    def PullIfNoRateUp(self):
        self.PullSelected(np.argwhere(self.RateUpAcquired == 0))
    
    def PullMultipleTimes(self, Npulls):
        for i in range(Npulls):
            self.Pull()

    def PullUntilRateUp(self):
        while(not(self.RateUpAcquired.all())):
            self.PullIfNoRateUp()

    def Reduce(self, op):
        return op(self.TotalPulls-self.StartingPulls), op(self.RateUpCopiesCount), op(self.OffBanner6StarCount)

    # def PullUntilXRateUp(self, nRateUps):
    #     while self.RateUpCopiesCount < nRateUps:
    #         self.Pull()

    # def Reset(self):
    #     self.SixStarDropPity = self.StartingSixStarDropPity
    #     self.RateUpCopiesCount = 0
    #     self.PullsTowardsGuarantee = 0
    #     self.TotalPulls = self.StartingPulls
    #     self.RateUpAcquired = self.RateUpAcquiredFromStart


if __name__ == "__main__":
    N = int(1e6)
    Gacha = EndfieldGacha(N)

    Gacha.PullUntilRateUp()

    avgpulls,_,__ = Gacha.Reduce(np.mean)

    print(avgpulls)