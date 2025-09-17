import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TechStackAgentService, TechStackParams, Topic, AgentMessage } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';
import { ToastComponent } from '../shared/toast/toast.component';
import { Toast } from '../../models/interface/toast';
import { Observable } from 'rxjs';
import { Router } from '@angular/router';
import { DragDropModule, CdkDragDrop, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';

// Define skill level types for better type safety
type Level = 'beginner' | 'intermediate' | 'advanced';

// Extended Topic interface with selection state and drag-drop support
interface SelectableTopic extends Topic {
  selected: boolean;
  assignedLevel?: Level; // Track which skill level bucket the topic is assigned to
}

@Component({
  selector: 'app-techstack-form',
  templateUrl: './techstack-form.component.html',
  styleUrls: ['./techstack-form.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, ToastComponent, DragDropModule, BackButtonComponent]
})
export class TechStackFormComponent implements OnInit {
  topicDescription: string = '';
  params: TechStackParams = {
    name: '',
    description:this.topicDescription
  };

  topics: SelectableTopic[] = [];
  log: string[] = [];
  reviewIteration = 0;
  wsConnected = false;
  showControls = false;
  feedback: string = '';
  toasts$: Observable<Toast[]>;
  isLoading: boolean = false; // Controls loader visibility

  // Conditional rendering state
  isCapabilityLeader: boolean = false;
  isCollaborator: boolean = false;
  topicsExistForLeader: boolean = false;
  
  // Topic selection properties - level-specific select all states
  selectAllBeginner = false;
  selectAllIntermediate = false;
  selectAllAdvanced = false;

  // Drag-and-drop bucket arrays for assigned topics
  assignedBeginnerTopics: SelectableTopic[] = [];
  assignedIntermediateTopics: SelectableTopic[] = [];
  assignedAdvancedTopics: SelectableTopic[] = [];

  constructor(
    private agent: TechStackAgentService,
    private toastService: ToastService,
    private router: Router
  ) {
    this.toasts$ = this.toastService.toasts$;
  }

  connect() {
    this.log = [];
    this.topics = [];
    this.wsConnected = true;
    this.feedback = '';
    this.isLoading = true; // Show loader when starting generation
    
    this.agent.connect(this.params).subscribe({
      next: (msg: AgentMessage) => {
        this.log.push(JSON.stringify(msg, null, 2));
        this.isLoading = false; // Hide loader on any response
        if (msg.type === 'review') {
          this.topics = this.addSelectionState(msg.content);
          this.reviewIteration = msg.iteration || 1;
          this.showControls = true;
        } else if (msg.type === 'final') {
          const finalTopics = msg.content.topics ? msg.content.topics : msg.content;
          this.topics = this.addSelectionState(finalTopics);
          this.showControls = false;
          this.wsConnected = false;
          this.toastService.showSuccess('Learning concepts generated successfully!');
        } else if (msg.type === 'error') {
          this.showControls = false;
          this.wsConnected = false;
          this.toastService.showError('Failed to generate learning concepts. Please try again.');
        }
      },
      error: (error) => {
        this.wsConnected = false;
        this.showControls = false;
        this.isLoading = false; // Hide loader on error
        this.toastService.showError('Connection error. Please check your network and try again.');
      }
    });
  }

  sendDecision(decision: string, feedback?: string) {
    this.agent.sendDecision(decision, feedback);
    this.log.push(`Sent decision: ${decision}${feedback ? ' with feedback: ' + feedback : ''}`);
  }

  closeWs() {
    this.agent.close();
    this.wsConnected = false;
    this.showControls = false;
  }

  get formattedTopicsJson(): string {
    const grouped: { [key: string]: string[] } = {
      beginner: [],
      intermediate: [],
      advanced: []
    };
    for (const topic of this.topics) {
      const level = (topic.level || '').toLowerCase();
      if (grouped[level]) {
        grouped[level].push(topic.name);
      }
    }
    return JSON.stringify(grouped, null, 2);
  }

  // Helper method to add selection state to topics
  private addSelectionState(topics: Topic[]): SelectableTopic[] {
    return topics.map(topic => ({
      ...topic,
      selected: false
    }));
  }

  getTopicsByLevel(level: string): SelectableTopic[] {
    return this.topics.filter(topic => topic.level === level);
  }

  saveTopics() {
    try {
      // Only save selected topics, not all topics
      const selectedTopics = this.topics.filter(topic => topic.selected);
      
      if (selectedTopics.length === 0) {
        this.toastService.showWarning('Please select at least one topic to save.');
        return;
      }
      
      // Group selected topics by level for better organization
      const selectedByLevel = {
        beginner: selectedTopics.filter(topic => topic.level === 'beginner'),
        intermediate: selectedTopics.filter(topic => topic.level === 'intermediate'),
        advanced: selectedTopics.filter(topic => topic.level === 'advanced')
      };
      
      const topicsData = {
        topicName: this.params.name,
        description: this.topicDescription,
        selectedTopics: selectedTopics.map(topic => ({
          name: topic.name,
          level: topic.level
        })),
        selectedByLevel: selectedByLevel,
        totalSelected: selectedTopics.length,
        selectionSummary: {
          beginner: selectedByLevel.beginner.length,
          intermediate: selectedByLevel.intermediate.length,
          advanced: selectedByLevel.advanced.length
        },
        generatedAt: new Date().toISOString(),
        created_by: this.agent.getUserId()
      };
      
      console.log('Saving only selected topics to DB:', topicsData);
      
      // Call API to save selected topics to database
      this.agent.saveSelectedTopics(topicsData).subscribe({
        next: (response) => {
          console.log('Topics saved successfully:', response);
          this.toastService.showSuccess(`Successfully saved ${response.saved_topics_count} new topics to database! (Total selected: ${selectedTopics.length})`);
        },
        error: (error) => {
          console.error('Error saving topics:', error);
          const errorMessage = error?.error?.detail || 'Failed to save topics to database';
          this.toastService.showError(errorMessage);
        }
      });
    } catch (error) {
      this.toastService.showError('Failed to save topics. Please try again.');
    }
  }

  approveTopics() {
    this.sendDecision('approve');
    this.showControls = false;
    this.toastService.showInfo('Topics approved. Generating final version...');
  }

  approveAndSaveTopics() {
    if (this.getSelectedTopicsCount() === 0) {
      this.toastService.showWarning('Please select at least one topic to save.');
      return;
    }

    // Save the selected topics first, before sending the decision
    this.saveSelectedTopicsToDatabase();

    // Then approve the topics
    this.sendDecision('approve');
    this.showControls = false;
    this.toastService.showInfo('Topics approved and saved successfully!');
  }

  private saveSelectedTopicsToDatabase() {
    const selectedTopics = this.topics.filter(topic => topic.selected);
    
    if (selectedTopics.length === 0) {
      this.toastService.showWarning('No topics selected to save.');
      return;
    }

    const topicsData = {
      topicName: this.params.name,
      description: this.topicDescription,
      selectedTopics: selectedTopics.map(topic => ({
        name: topic.name,
        level: topic.level
      })),
      totalSelected: selectedTopics.length,
      created_by: this.agent.getUserId()
    };

    try {
      this.agent.saveSelectedTopics(topicsData).subscribe({
        next: (response: any) => {
          this.toastService.showSuccess(`Successfully saved ${response.saved_topics_count || selectedTopics.length} topics to database!`);
          this.router.navigate(["capability-leader-dashboard"]);
        },
        error: (error) => {
          console.error('Error saving topics:', error);
          this.toastService.showError('Failed to save topics to database. Please try again.');
        }
      });
    } catch (error) {
      this.toastService.showError('Failed to save topics. Please try again.');
    }
  }

  regenerateTopics() {
    if (!this.feedback.trim()) {
      this.toastService.showWarning('Please provide feedback for Regenerate.');
      return;
    }
    this.isLoading = true; // Show loader while waiting for regenerate response
    this.sendDecision('feedback', this.feedback);
    console.log(this.feedback)
    this.feedback = '';
    this.toastService.showInfo('Regenerating topics...');
  }

  rejectTopics() {
    // Clear topics and assignment buckets before regenerating
    this.topics = [];
    this.assignedBeginnerTopics = [];
    this.assignedIntermediateTopics = [];
    this.assignedAdvancedTopics = [];
    const feedbackText = 'Please regenerate the topics';
    this.isLoading = true; // Show loader while waiting for reject & regenerate response
    this.sendDecision('reject', feedbackText);
    this.feedback = '';
    this.toastService.showInfo('Topics rejected. Regenerating...');
  }

  onToastDismiss(toastId: string) {
    this.toastService.dismissToast(toastId);
  }

  // Topic selection methods - refactored for proper level-scoped selection
  onTopicSelectionChange(topic: SelectableTopic) {
    topic.selected = !topic.selected;
    this.updateSelectAllStates();
  }

  onSelectAllBeginner() {
    this.selectAllBeginner = !this.selectAllBeginner;
    const beginnerTopics = this.getTopicsByLevel('beginner');
    beginnerTopics.forEach(topic => {
      topic.selected = this.selectAllBeginner;
    });
  }

  onSelectAllIntermediate() {
    this.selectAllIntermediate = !this.selectAllIntermediate;
    const intermediateTopics = this.getTopicsByLevel('intermediate');
    intermediateTopics.forEach(topic => {
      topic.selected = this.selectAllIntermediate;
    });
  }

  onSelectAllAdvanced() {
    this.selectAllAdvanced = !this.selectAllAdvanced;
    const advancedTopics = this.getTopicsByLevel('advanced');
    advancedTopics.forEach(topic => {
      topic.selected = this.selectAllAdvanced;
    });
  }

  updateSelectAllStates() {
    const beginnerTopics = this.getTopicsByLevel('beginner');
    const intermediateTopics = this.getTopicsByLevel('intermediate');
    const advancedTopics = this.getTopicsByLevel('advanced');
    
    this.selectAllBeginner = beginnerTopics.length > 0 && beginnerTopics.every(topic => topic.selected);
    this.selectAllIntermediate = intermediateTopics.length > 0 && intermediateTopics.every(topic => topic.selected);
    this.selectAllAdvanced = advancedTopics.length > 0 && advancedTopics.every(topic => topic.selected);
  }

  isTopicSelected(topic: SelectableTopic): boolean {
    return topic.selected;
  }

  getSelectedTopicsCount(): number {
    return this.topics.filter(topic => topic.selected).length;
  }

  // Helper method to get selected topics by specific level
  getSelectedTopicsByLevel(level: Level): SelectableTopic[] {
    return this.topics.filter(topic => topic.level === level && topic.selected);
  }

  // Helper method to check if any topics are selected in a specific level
  hasSelectedTopicsInLevel(level: Level): boolean {
    return this.getSelectedTopicsByLevel(level).length > 0;
  }

  userName: string = '';

  ngOnInit(): void {
    this.userName = localStorage.getItem('username') || '';

    // If capability leader, stay on techstack-form for topic creation/drag-drop
  }

  // Back button handler for shared component
  returnToDashboard(): void {
    this.router.navigate(['/capability-leader-dashboard']);
  }

  // Drag and drop event handlers for enhanced visual feedback
  onDragStarted(event: any): void {
    // Add visual feedback when drag starts
    const dragElement = event.source.element.nativeElement;
    dragElement.classList.add('drag-active');
    // Removed drop zone glow effect for static drag-and-drop experience
  }

  onDragEnded(event: any): void {
    // Remove visual feedback when drag ends
    const dragElement = event.source.element.nativeElement;
    dragElement.classList.remove('drag-active');
    // Removed drop zone glow effect for static drag-and-drop experience
  }

  // Enhanced drop handler with visual feedback
  onTopicDrop(event: CdkDragDrop<SelectableTopic[]>, targetLevel: Level): void {
    // Add success animation to the drop container
    const dropContainer = event.container.element.nativeElement;
    dropContainer.classList.add('success-drop');
    setTimeout(() => {
      dropContainer.classList.remove('success-drop');
    }, 600);

    if (event.previousContainer === event.container) {
      // Reordering within the same container
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      // Multi-selection drag-and-drop support
      const draggedTopic = event.item.data as SelectableTopic;
      let topicsToMove: SelectableTopic[] = [];

      // If the dragged topic is selected, move all selected topics from the source container
      if (draggedTopic.selected) {
        // Only move selected topics that are in the source container
        topicsToMove = event.previousContainer.data.filter(t => t.selected);
      } else {
        // Move only the dragged topic
        topicsToMove = [draggedTopic];
      }

      // Remove topics from previous container
      topicsToMove.forEach(topic => {
        const idx = event.previousContainer.data.findIndex(t => t.id === topic.id);
        if (idx !== -1) {
          event.previousContainer.data.splice(idx, 1);
        }
      });

      // Insert topics into target container at the drop index
      // If dropping multiple, insert all at the drop index
      event.container.data.splice(event.currentIndex, 0, ...topicsToMove);

      // Update assignedLevel and selection state
      topicsToMove.forEach(topic => {
        topic.assignedLevel = targetLevel;
        topic.selected = true;
      });

      // Show success toast
      if (topicsToMove.length > 1) {
        this.toastService.showSuccess(`Moved ${topicsToMove.length} topics to ${targetLevel} level`);
      } else {
        this.toastService.showSuccess(`Topic "${topicsToMove[0].name}" assigned to ${targetLevel} level`);
      }
    }
  }

  // Helper method to get topic's current level
  private getTopicLevel(topic: SelectableTopic): Level | undefined {
    if (this.assignedBeginnerTopics.find(t => t.id === topic.id)) return 'beginner';
    if (this.assignedIntermediateTopics.find(t => t.id === topic.id)) return 'intermediate';
    if (this.assignedAdvancedTopics.find(t => t.id === topic.id)) return 'advanced';
    return undefined;
  }

  // Remove topic from bucket and return to original list
  removeFromBucket(topic: SelectableTopic, sourceLevel?: Level): void {
    // If sourceLevel is provided, remove from specific bucket
    if (sourceLevel) {
      switch (sourceLevel) {
        case 'beginner':
          const beginnerIndex = this.assignedBeginnerTopics.findIndex(t => t.id === topic.id);
          if (beginnerIndex !== -1) {
            this.assignedBeginnerTopics.splice(beginnerIndex, 1);
          }
          break;
        case 'intermediate':
          const intermediateIndex = this.assignedIntermediateTopics.findIndex(t => t.id === topic.id);
          if (intermediateIndex !== -1) {
            this.assignedIntermediateTopics.splice(intermediateIndex, 1);
          }
          break;
        case 'advanced':
          const advancedIndex = this.assignedAdvancedTopics.findIndex(t => t.id === topic.id);
          if (advancedIndex !== -1) {
            this.assignedAdvancedTopics.splice(advancedIndex, 1);
          }
          break;
      }
    } else {
      // Find which bucket the topic is in and remove it
      const buckets = [
        { array: this.assignedBeginnerTopics, level: 'beginner' as Level },
        { array: this.assignedIntermediateTopics, level: 'intermediate' as Level },
        { array: this.assignedAdvancedTopics, level: 'advanced' as Level }
      ];

      for (const bucket of buckets) {
        const index = bucket.array.findIndex(t => t.id === topic.id);
        if (index !== -1) {
          bucket.array.splice(index, 1);
          break;
        }
      }
    }

    // Reset topic properties
    topic.assignedLevel = undefined;
    topic.selected = false;
  }

  // Get topics that are not assigned to any bucket (available for dragging)
  getAvailableTopicsByLevel(level: Level): SelectableTopic[] {
    return this.topics.filter(topic => 
      topic.level === level && !topic.assignedLevel
    );
  }

  // Get assigned topics for a specific level bucket
  getAssignedTopicsByLevel(level: Level): SelectableTopic[] {
    switch (level) {
      case 'beginner':
        return this.assignedBeginnerTopics;
      case 'intermediate':
        return this.assignedIntermediateTopics;
      case 'advanced':
        return this.assignedAdvancedTopics;
      default:
        return [];
    }
  }

  // Get total count of assigned topics across all levels
  getTotalAssignedTopicsCount(): number {
    return this.assignedBeginnerTopics.length + 
           this.assignedIntermediateTopics.length + 
           this.assignedAdvancedTopics.length;
  }

  // Check if any topics are assigned to buckets
  hasAssignedTopics(): boolean {
    return this.getTotalAssignedTopicsCount() > 0;
  }

  /**
   * Clear all assignment buckets (optional utility method)
   * Used after saving or when resetting the topic assignments
   */
  private clearAllBuckets() {
    this.assignedBeginnerTopics = [];
    this.assignedIntermediateTopics = [];
    this.assignedAdvancedTopics = [];
    
    // Reset assignedLevel property for all topics
    this.topics.forEach(topic => {
      delete topic.assignedLevel;
    });
    
    // Notify user that buckets have been cleared
    this.toastService.showInfo('All topic assignments have been cleared.');
  }

  /**
   * Save selected topics from drag-and-drop buckets to database
   * This method handles the new "Save Selected Topics" button functionality
   * Optimized for better performance with drag-and-drop integration
   */
  saveSelectedTopics() {
    // Check if there are any assigned topics in the buckets
    const totalAssigned = this.getTotalAssignedTopicsCount();
    
    if (totalAssigned === 0) {
      this.toastService.showWarning('Please assign at least one topic to a skill level before saving.');
      return;
    }

    // Show confirmation dialog before saving
    const confirmed = confirm(`Are you sure you want to save ${totalAssigned} assigned topics to the database?`);
    
    if (!confirmed) {
      return;
    }

    // Collect all assigned topics from all buckets - avoid unnecessary object spreading
    // Use direct references to the bucket arrays for better performance
    const assignedTopics: SelectableTopic[] = [];
    
    // Add topics from each bucket with their respective levels
    this.assignedBeginnerTopics.forEach(topic => {
      assignedTopics.push({
        ...topic,
        assignedLevel: 'beginner'
      });
    });
    
    this.assignedIntermediateTopics.forEach(topic => {
      assignedTopics.push({
        ...topic,
        assignedLevel: 'intermediate'
      });
    });
    
    this.assignedAdvancedTopics.forEach(topic => {
      assignedTopics.push({
        ...topic,
        assignedLevel: 'advanced'
      });
    });

    // Prepare data for backend API - optimize the mapping operation
    const topicsData = {
      topicName: this.params.name,
      description: this.topicDescription,
      selectedTopics: assignedTopics.map(topic => ({
        id: topic.id, // Include ID for better tracking
        name: topic.name,
        level: topic.assignedLevel || topic.level // Use assigned level or fallback to original level
      })),
      totalSelected: assignedTopics.length,
      created_by: this.agent.getUserId()
    };

    try {
      // Show loading indicator
      this.toastService.showInfo('Saving topics to database...');
      
      // Call the backend API to save topics
      this.agent.saveSelectedTopics(topicsData).subscribe({
        next: (response: any) => {
          this.toastService.showSuccess(`Successfully saved ${response.saved_topics_count || assignedTopics.length} topics to database!`);
          
          // Navigate to dashboard after successful save
          this.router.navigate(["capability-leader-dashboard"]);
        },
        error: (error) => {
          console.error('Error saving assigned topics:', error);
          this.toastService.showError('Failed to save topics to database. Please try again.');
        }
      });
    } catch (error) {
      console.error('Exception while saving topics:', error);
      this.toastService.showError('Failed to save topics. Please try again.');
    }
  }

  // Helper method for trackBy function to improve rendering performance
  trackByTopicId(index: number, topic: SelectableTopic): string {
    return topic.id || topic.name;
  }
}
