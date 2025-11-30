import { useState, useEffect, useRef } from 'react';
import { Mic, Send, Loader2, Volume2, Database, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { sendTextQuery, transcribeAudio, synthesizeSpeech, Message } from './services/api';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { FactsManager } from './components/FactsManager';
import { ToolCallsDisplay } from './components/ToolCallsDisplay';
import { FeedbackButtons } from './components/FeedbackButtons';
import { LearningDashboard } from './components/LearningDashboard';

interface MessageWithTools extends Message {
  toolCalls?: Array<{ tool: string; args: Record<string, unknown> }>;
  toolResults?: Array<{ tool: string; result: unknown }>;
  model?: string;
  provider?: string;
  query?: string;
}

function App() {
  const [messages, setMessages] = useState<MessageWithTools[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();
  const { state: recordingState, error: recordingError, startRecording, stopRecording } = useAudioRecorder();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (recordingError) {
      toast({
        title: 'Mikrofon-Fehler',
        description: recordingError,
        variant: 'destructive',
      });
    }
  }, [recordingError, toast]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: MessageWithTools = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const conversationHistory = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await sendTextQuery(text, conversationHistory);
      const assistantMessage: MessageWithTools = { 
        role: 'assistant', 
        content: response.response,
        toolCalls: response.tool_calls,
        toolResults: response.tool_results,
        model: (response as any).llm_metadata?.model,
        provider: (response as any).llm_metadata?.provider,
        query: text
      };
      setMessages((prev) => [...prev, assistantMessage]);

      const audioBlob = await synthesizeSpeech(response.response);
      playAudio(audioBlob);
    } catch (error) {
      console.error('Error processing message:', error);
      toast({
        title: 'Fehler',
        description: error instanceof Error ? error.message : 'Ein Fehler ist aufgetreten',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleMicClick = async () => {
    if (recordingState === 'idle') {
      await startRecording();
    } else if (recordingState === 'recording') {
      setIsLoading(true);
      try {
        const audioBlob = await stopRecording();
        
        const transcription = await transcribeAudio(audioBlob);
        
        await handleSendMessage(transcription.text);
      } catch (error) {
        console.error('Error processing voice input:', error);
        toast({
          title: 'Fehler',
          description: error instanceof Error ? error.message : 'Spracherkennung fehlgeschlagen',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const playAudio = (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    
    audio.onplay = () => setIsPlayingAudio(true);
    audio.onended = () => {
      setIsPlayingAudio(false);
      URL.revokeObjectURL(url);
    };
    audio.onerror = () => {
      setIsPlayingAudio(false);
      URL.revokeObjectURL(url);
      toast({
        title: 'Audio-Fehler',
        description: 'Audio konnte nicht abgespielt werden',
        variant: 'destructive',
      });
    };
    
    audio.play().catch(err => {
      console.error('Error playing audio:', err);
      setIsPlayingAudio(false);
      URL.revokeObjectURL(url);
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900/20 to-purple-900/20 flex flex-col">
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">J</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Jarvis AI</h1>
            <p className="text-sm text-gray-400">Ihr intelligenter Assistent</p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-hidden max-w-6xl w-full mx-auto px-4 py-6">
        <Tabs defaultValue="chat" className="h-full flex flex-col">
          <TabsList className="bg-gray-900/50 border border-gray-800 mb-4">
            <TabsTrigger value="chat" className="data-[state=active]:bg-blue-600">
              Chat
            </TabsTrigger>
            <TabsTrigger value="facts" className="data-[state=active]:bg-blue-600">
              <Database className="w-4 h-4 mr-2" />
              Fakten
            </TabsTrigger>
            <TabsTrigger value="learning" className="data-[state=active]:bg-blue-600">
              <Brain className="w-4 h-4 mr-2" />
              Lernen
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="flex-1 overflow-hidden flex flex-col mt-0">
            <div className="flex-1 overflow-hidden flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {messages.length === 0 && (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center space-y-4">
                      <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto">
                        <span className="text-white font-bold text-3xl">J</span>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-white mb-2">Willkommen bei Jarvis</h2>
                        <p className="text-gray-400">Stellen Sie eine Frage oder nutzen Sie das Mikrofon</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] space-y-2 ${message.role === 'user' ? '' : 'w-full max-w-[80%]'}`}>
                      <Card
                        className={`p-4 ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white border-blue-500'
                            : 'bg-gray-800 text-white border-gray-700'
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      </Card>
                      {message.role === 'assistant' && (
                        <>
                          <ToolCallsDisplay 
                            toolCalls={message.toolCalls} 
                            toolResults={message.toolResults}
                          />
                          <FeedbackButtons
                            query={message.query || ''}
                            response={message.content}
                            model={message.model}
                            provider={message.provider}
                          />
                        </>
                      )}
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <Card className="bg-gray-800 text-white border-gray-700 p-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Jarvis denkt nach...</span>
                      </div>
                    </Card>
                  </div>
                )}
                
                {isPlayingAudio && (
                  <div className="flex justify-start">
                    <Card className="bg-gray-800 text-white border-gray-700 p-4">
                      <div className="flex items-center gap-2">
                        <Volume2 className="w-4 h-4 animate-pulse" />
                        <span className="text-sm">Jarvis spricht...</span>
                      </div>
                    </Card>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-lg p-4">
                <div className="flex gap-3 items-end">
                  <div className="flex-1">
                    <Input
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(inputText)}
                      placeholder="Nachricht an Jarvis..."
                      disabled={isLoading || recordingState !== 'idle'}
                      className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                    />
                  </div>
                  
                  <Button
                    onClick={() => handleSendMessage(inputText)}
                    disabled={!inputText.trim() || isLoading || recordingState !== 'idle'}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    onClick={handleMicClick}
                    disabled={isLoading || recordingState === 'processing'}
                    className={`${
                      recordingState === 'recording'
                        ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                        : 'bg-purple-600 hover:bg-purple-700'
                    }`}
                  >
                    {recordingState === 'processing' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Mic className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                
                <p className="text-xs text-gray-500 mt-2 text-center">
                  {recordingState === 'recording'
                    ? 'Aufnahme läuft... Klicken Sie erneut zum Beenden'
                    : 'Drücken Sie das Mikrofon für Spracheingabe'}
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="facts" className="flex-1 overflow-y-auto mt-0">
            <FactsManager />
          </TabsContent>

          <TabsContent value="learning" className="flex-1 overflow-y-auto mt-0">
            <LearningDashboard />
          </TabsContent>
        </Tabs>
      </div>
      
      <Toaster />
    </div>
  );
}

export default App;
