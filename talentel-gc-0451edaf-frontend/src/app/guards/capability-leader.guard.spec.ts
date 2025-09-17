import { TestBed } from '@angular/core/testing';
import { CanActivateFn } from '@angular/router';

import { capabilityLeaderGuard } from './capability-leader.guard';

describe('capabilityLeaderGuard', () => {
  const executeGuard: CanActivateFn = (...guardParameters) => 
      TestBed.runInInjectionContext(() => capabilityLeaderGuard(...guardParameters));

  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  it('should be created', () => {
    expect(executeGuard).toBeTruthy();
  });
});
