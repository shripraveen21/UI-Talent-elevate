import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SkillUpgradeComponent } from './skill-upgrade.component';

describe('SkillUpgradeComponent', () => {
  let component: SkillUpgradeComponent;
  let fixture: ComponentFixture<SkillUpgradeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SkillUpgradeComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SkillUpgradeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
