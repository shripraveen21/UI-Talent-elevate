import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FeedbackResultComponent } from './feedback-result.component';

describe('FeedbackResultComponent', () => {
  let component: FeedbackResultComponent;
  let fixture: ComponentFixture<FeedbackResultComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FeedbackResultComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FeedbackResultComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
