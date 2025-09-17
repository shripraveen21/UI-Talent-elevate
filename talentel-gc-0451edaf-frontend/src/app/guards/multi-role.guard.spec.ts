import { TestBed } from '@angular/core/testing';
import { CanActivateFn } from '@angular/router';

import { multiRoleGuard } from './multi-role.guard';

describe('multiRoleGuard', () => {
  const executeGuard: CanActivateFn = (...guardParameters) => 
      TestBed.runInInjectionContext(() => multiRoleGuard(...guardParameters));

  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  it('should be created', () => {
    expect(executeGuard).toBeTruthy();
  });
});
