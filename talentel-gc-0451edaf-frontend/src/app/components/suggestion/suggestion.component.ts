import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { YourSuggestionService, SuggestionForLeader } from '../../services/suggestion/suggestion.service';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar} from '@angular/material/snack-bar';
import { ConfirmDialogComponent } from './confirm-dialog.component';
@Component({
  selector: 'app-suggestion',
  templateUrl: './suggestion.component.html',
  standalone: true,
  imports: [CommonModule]
})
export class SuggestionComponent implements OnInit {
  suggestions: SuggestionForLeader[] = [];
  isCapabilityLeader: boolean = false;
  userId: number | null = null;

  constructor(private suggestionService: YourSuggestionService, 
    private dialog: MatDialog,
  private snackBar: MatSnackBar) {}

  ngOnInit(): void {
    // Get user info from localStorage
    const userJson = localStorage.getItem('user');
    let userRole = '';
    if (userJson) {
      try {
        const userObj = JSON.parse(userJson);
        this.userId = userObj.user_id;
        userRole = userObj.role;
      } catch (err) {
        console.error('[SuggestionComponent] Error parsing user:', err);
      }
    }

    this.isCapabilityLeader = userRole === 'CapabilityLeader';

    if (this.isCapabilityLeader && this.userId) {
      this.suggestionService.getSuggestionsForLeader(this.userId).subscribe({
        next: (data) => {
          this.suggestions = data;
        },
        error: (err) => {
          console.error('[SuggestionComponent] Error fetching suggestions:', err);
        }
      });
    }
    
  }
  deleteSuggestion(suggestionId: number): void {
  const dialogRef = this.dialog.open(ConfirmDialogComponent);

  dialogRef.afterClosed().subscribe(result => {
    if (result) {
      this.suggestionService.deleteSuggestion(suggestionId).subscribe({
        next: () => {
          this.suggestions = this.suggestions.filter(s => s.id !== suggestionId);
          this.snackBar.open('Suggestion deleted', 'Close', {
            duration: 3000,
            panelClass: ['snackbar-success']
          });
        },
        error: () => {
          this.snackBar.open('Failed to delete suggestion', 'Close', {
            duration: 3000,
            panelClass: ['snackbar-error']
          });
        }
      });
    }
  });
}
}
