import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Brain, TrendingUp, MessageSquare, AlertCircle } from 'lucide-react';
import { getLearningStatistics, type LearningStatistics } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

export function LearningDashboard() {
  const [stats, setStats] = useState<LearningStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const data = await getLearningStatistics();
      setStats(data);
    } catch (error) {
      console.error('Error loading statistics:', error);
      toast({
        title: 'Fehler',
        description: 'Statistiken konnten nicht geladen werden',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-gray-800 border-gray-700 p-6">
        <p className="text-gray-400">Lade Statistiken...</p>
      </Card>
    );
  }

  if (!stats) {
    return null;
  }

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-500';
    if (rating >= 3.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-6 h-6 text-purple-500" />
        <h2 className="text-xl font-bold text-white">Lern-Statistiken</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Feedback */}
        <Card className="bg-gray-800 border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/20 p-3 rounded-lg">
              <MessageSquare className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Gesamt Feedback</p>
              <p className="text-2xl font-bold text-white">{stats.total_feedback}</p>
            </div>
          </div>
        </Card>

        {/* Average Rating */}
        <Card className="bg-gray-800 border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="bg-purple-500/20 p-3 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Durchschnitt</p>
              <p className={`text-2xl font-bold ${getRatingColor(stats.average_rating)}`}>
                {stats.average_rating.toFixed(1)} ⭐
              </p>
            </div>
          </div>
        </Card>

        {/* Total Corrections */}
        <Card className="bg-gray-800 border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="bg-orange-500/20 p-3 rounded-lg">
              <AlertCircle className="w-6 h-6 text-orange-500" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Korrekturen</p>
              <p className="text-2xl font-bold text-white">{stats.total_corrections}</p>
            </div>
          </div>
        </Card>

        {/* Recent Feedback */}
        <Card className="bg-gray-800 border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="bg-green-500/20 p-3 rounded-lg">
              <Brain className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Letzte 7 Tage</p>
              <p className="text-2xl font-bold text-white">{stats.recent_feedback_7d}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Rating Distribution */}
      <Card className="bg-gray-800 border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Bewertungsverteilung</h3>
        <div className="space-y-3">
          {[5, 4, 3, 2, 1].map((rating) => {
            const count = stats.rating_distribution[rating] || 0;
            const percentage = stats.total_feedback > 0 
              ? (count / stats.total_feedback) * 100 
              : 0;
            
            return (
              <div key={rating} className="flex items-center gap-3">
                <span className="text-sm text-gray-400 w-12">{rating} ⭐</span>
                <div className="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      rating >= 4 ? 'bg-green-500' : rating === 3 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className="text-sm text-gray-400 w-16 text-right">
                  {count} ({percentage.toFixed(0)}%)
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Learning Info */}
      <Card className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 border-purple-700/50 p-6">
        <div className="flex items-start gap-3">
          <Brain className="w-6 h-6 text-purple-400 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Wie ich lerne</h3>
            <p className="text-sm text-gray-300 leading-relaxed">
              Dein Feedback hilft mir, besser zu werden! Jede Bewertung und Korrektur wird gespeichert 
              und bei zukünftigen Anfragen berücksichtigt. Negative Bewertungen und Korrekturen werden 
              automatisch in meinen Prompt integriert, damit ich ähnliche Fehler nicht wiederhole.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
