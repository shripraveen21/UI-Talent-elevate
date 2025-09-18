import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
@Component({
  selector: 'app-backbutton',
  imports:[CommonModule],
  templateUrl: './backbutton.component.html',
  styleUrls: ['./backbutton.component.css'],
  standalone: true
})
export class BackButtonComponent {
  @Input() label: string = 'Return to Dashboard';
  @Input() icon: boolean = true;
  @Input() clickHandler: () => void = () => {};
}
