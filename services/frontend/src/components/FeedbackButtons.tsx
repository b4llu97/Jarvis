import { useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { submitFeedback, submitCorrection } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface FeedbackButtonsProps {
  query: string;
  response: string;
  model?: string;
  provider?: string;
}

export function FeedbackButtons({ query, response, model, provider }: FeedbackButtonsProps) {
  const [feedbackGiven, setFeedbackGiven] = useState<'positive' | 'negative' | null>(null);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [showCorrectionDialog, setShowCorrectionDialog] = useState(false);
  const [comment, setComment] = useState('');
  const [correction, setCorrection] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handlePositiveFeedback = async () => {
    if (feedbackGiven) return;
    
    setIsSubmitting(true);
    try {
      await submitFeedback({
        query,
        response,
        rating: 5,
        model,
        provider,
      });
      setFeedbackGiven('positive');
      toast({
        title: 'Danke für dein Feedback!',
        description: 'Deine positive Bewertung hilft mir zu lernen.',
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast({
        title: 'Fehler',
        description: 'Feedback konnte nicht gespeichert werden',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNegativeFeedback = () => {
    if (feedbackGiven) return;
    setShowCommentDialog(true);
  };

  const handleSubmitComment = async () => {
    setIsSubmitting(true);
    try {
      await submitFeedback({
        query,
        response,
        rating: 1,
        comment: comment || undefined,
        model,
        provider,
      });
      setFeedbackGiven('negative');
      setShowCommentDialog(false);
      toast({
        title: 'Danke für dein Feedback!',
        description: 'Ich werde aus diesem Fehler lernen.',
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast({
        title: 'Fehler',
        description: 'Feedback konnte nicht gespeichert werden',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
      setComment('');
    }
  };

  const handleCorrection = () => {
    setShowCorrectionDialog(true);
  };

  const handleSubmitCorrection = async () => {
    if (!correction.trim()) {
      toast({
        title: 'Fehler',
        description: 'Bitte gib die richtige Antwort ein',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await submitCorrection({
        query,
        wrong_response: response,
        correct_response: correction,
      });
      
      // Also submit negative feedback
      await submitFeedback({
        query,
        response,
        rating: 1,
        comment: 'Korrektur eingereicht',
        model,
        provider,
      });
      
      setFeedbackGiven('negative');
      setShowCorrectionDialog(false);
      toast({
        title: 'Korrektur gespeichert!',
        description: 'Ich werde diese Korrektur in Zukunft berücksichtigen.',
      });
    } catch (error) {
      console.error('Error submitting correction:', error);
      toast({
        title: 'Fehler',
        description: 'Korrektur konnte nicht gespeichert werden',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
      setCorrection('');
    }
  };

  return (
    <>
      <div className="flex items-center gap-2 mt-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handlePositiveFeedback}
          disabled={feedbackGiven !== null || isSubmitting}
          className={`h-8 px-2 ${
            feedbackGiven === 'positive'
              ? 'text-green-500 hover:text-green-600'
              : 'text-gray-400 hover:text-green-500'
          }`}
        >
          {feedbackGiven === 'positive' ? (
            <Check className="w-4 h-4 mr-1" />
          ) : (
            <ThumbsUp className="w-4 h-4 mr-1" />
          )}
          Hilfreich
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleNegativeFeedback}
          disabled={feedbackGiven !== null || isSubmitting}
          className={`h-8 px-2 ${
            feedbackGiven === 'negative'
              ? 'text-red-500 hover:text-red-600'
              : 'text-gray-400 hover:text-red-500'
          }`}
        >
          {feedbackGiven === 'negative' ? (
            <Check className="w-4 h-4 mr-1" />
          ) : (
            <ThumbsDown className="w-4 h-4 mr-1" />
          )}
          Nicht hilfreich
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleCorrection}
          disabled={feedbackGiven !== null || isSubmitting}
          className="h-8 px-2 text-gray-400 hover:text-blue-500"
        >
          <MessageSquare className="w-4 h-4 mr-1" />
          Korrigieren
        </Button>
      </div>

      {/* Comment Dialog */}
      <Dialog open={showCommentDialog} onOpenChange={setShowCommentDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>Was war das Problem?</DialogTitle>
            <DialogDescription className="text-gray-400">
              Dein Feedback hilft mir, besser zu werden. Was war an der Antwort nicht hilfreich?
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional: Beschreibe das Problem..."
            className="bg-gray-800 border-gray-700 text-white min-h-[100px]"
          />
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => {
                setShowCommentDialog(false);
                setComment('');
              }}
              disabled={isSubmitting}
            >
              Abbrechen
            </Button>
            <Button
              onClick={handleSubmitComment}
              disabled={isSubmitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? 'Wird gespeichert...' : 'Absenden'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Correction Dialog */}
      <Dialog open={showCorrectionDialog} onOpenChange={setShowCorrectionDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Korrektur eingeben</DialogTitle>
            <DialogDescription className="text-gray-400">
              Bitte gib die richtige Antwort ein. Ich werde daraus lernen.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">
                Falsche Antwort:
              </label>
              <div className="bg-gray-800 border border-gray-700 rounded-md p-3 text-sm text-gray-400 max-h-32 overflow-y-auto">
                {response}
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-300 mb-2 block">
                Richtige Antwort:
              </label>
              <Textarea
                value={correction}
                onChange={(e) => setCorrection(e.target.value)}
                placeholder="Gib hier die richtige Antwort ein..."
                className="bg-gray-800 border-gray-700 text-white min-h-[150px]"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => {
                setShowCorrectionDialog(false);
                setCorrection('');
              }}
              disabled={isSubmitting}
            >
              Abbrechen
            </Button>
            <Button
              onClick={handleSubmitCorrection}
              disabled={isSubmitting || !correction.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? 'Wird gespeichert...' : 'Korrektur absenden'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
