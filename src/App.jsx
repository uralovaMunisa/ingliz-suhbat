import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  BookOpen,
  CheckCircle2,
  Lightbulb,
  Globe,
  RotateCcw,
  BarChart2,
  HelpCircle,
  Award,
  Layers,
  Flame,
  Settings,
  X,
  Search,
  MessageSquare,
  ArrowRight,
  TrendingUp,
  Smile,
  ShieldCheck,
  Headphones
} from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState(null);
  const [speechRate, setSpeechRate] = useState(1.0); // 1.0 or 0.75 for slow

  // Shadowing & Pronunciation Practice State
  const [shadowingTarget, setShadowingTarget] = useState(null);
  const [shadowResult, setShadowResult] = useState(null);
  const [isShadowingListening, setIsShadowingListening] = useState(false);

  // Vocabulary Bank Modal State
  const [showVocabModal, setShowVocabModal] = useState(false);
  const [vocabList, setVocabList] = useState([]);
  const [vocabSearch, setVocabSearch] = useState('');
  const [activeVocabCard, setActiveVocabCard] = useState(null);

  // Settings Modal State
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [apiKeyStatus, setApiKeyStatus] = useState(null);
  const [savingKey, setSavingKey] = useState(false);

  // Uzbek translations cache
  const [uzbekTranslations, setUzbekTranslations] = useState({});
  const [loadingTranslation, setLoadingTranslation] = useState({});

  // Speaking Confidence & Stats
  const [stats, setStats] = useState({
    wordsSpoken: 0,
    sentencesCount: 0,
    vocabCount: 0,
    streak: 1,
    confidenceScore: 78
  });

  const [userProfile, setUserProfile] = useState({
    user_id: 1001,
    name: 'Friend',
    level: 'B1',
    goal: 'Daily conversation',
    mode: 'standard'
  });

  const chatEndRef = useRef(null);
  const speechRecognitionRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Initial load
  useEffect(() => {
    fetchProfile();
    fetchVocab();
    checkApiKeyStatus();

    setMessages([
      {
        id: 1,
        role: 'bot',
        text: "Hello! 👋 I'm **Emma**, your personal English conversation tutor and speaking coach.\n\nI'm here to help you speak with confidence, gently correct your grammar, and expand your vocabulary.\n\nWhat would you like to talk about today?",
        buttons: [
          { label: '☕ Hobbies & Free Time', action: () => handleSend('topic:hobbies') },
          { label: '✈️ Travel Memories', action: () => handleSend('topic:travel') },
          { label: '🎬 Movies & Music', action: () => handleSend('topic:entertainment') },
          { label: '📊 Choose English Level', action: () => handleSend('/level') }
        ]
      }
    ]);

    // Setup speech recognition if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (shadowingTarget) {
          evaluateShadowing(transcript, shadowingTarget);
        } else {
          setInputText((prev) => (prev ? prev + ' ' + transcript : transcript));
        }
      };

      recognition.onerror = () => {
        setIsListening(false);
        setIsShadowingListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        setIsShadowingListening(false);
      };

      speechRecognitionRef.current = recognition;
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`/api/user?user_id=${userProfile.user_id}`);
      const data = await res.json();
      if (data.user) {
        setUserProfile({
          user_id: data.user.user_id,
          name: data.user.name || 'Friend',
          level: data.user.level || 'B1',
          goal: data.user.goal || 'Daily conversation',
          mode: data.user.correction_mode || 'standard'
        });
      }
    } catch (e) {
      console.warn('Profile fetch fallback active');
    }
  };

  const fetchVocab = async () => {
    try {
      const res = await fetch(`/api/vocabulary?user_id=${userProfile.user_id}`);
      const data = await res.json();
      if (data.vocabulary) {
        setVocabList(data.vocabulary);
        setStats((prev) => ({ ...prev, vocabCount: data.vocabulary.length }));
      }
    } catch (e) {
      console.warn('Vocab fetch fallback active');
    }
  };

  const checkApiKeyStatus = async () => {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      setApiKeyStatus(data.has_key ? 'configured' : 'offline_mode');
    } catch (e) {
      setApiKeyStatus('offline_mode');
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKeyInput.trim()) return;
    setSavingKey(true);
    try {
      const res = await fetch('/api/set_key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKeyInput.trim() })
      });
      const data = await res.json();
      if (data.success) {
        setApiKeyStatus('configured');
        setShowSettingsModal(false);
        alert('✅ Gemini API Key saved successfully! Emma is powered by full Gemini AI.');
      } else {
        alert('Could not save key: ' + (data.error || 'Unknown error'));
      }
    } catch (e) {
      alert('Network error saving key.');
    } finally {
      setSavingKey(false);
    }
  };

  // Text-To-Speech (Native Web Speech API)
  const speakText = (text, msgId, rate = speechRate) => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in this browser.');
      return;
    }

    if (speakingMsgId === msgId) {
      window.speechSynthesis.cancel();
      setSpeakingMsgId(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Clean markdown before speaking
    const clean = text
      .replace(/[*_#`~]/g, '')
      .replace(/✏️|📚|❌|✅|💡|🎯|🎙️|👏|👩‍🏫|👋/g, '')
      .replace(/Correction:[\s\S]*$/, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'en-US';
    utterance.rate = rate; // 1.0 or 0.75 for clear beginner listening

    // Prefer high quality English voice if available
    const voices = window.speechSynthesis.getVoices();
    const enVoice = voices.find((v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha')));
    if (enVoice) utterance.voice = enVoice;

    utterance.onstart = () => setSpeakingMsgId(msgId);
    utterance.onend = () => setSpeakingMsgId(null);
    utterance.onerror = () => setSpeakingMsgId(null);

    window.speechSynthesis.speak(utterance);
  };

  // Speech Recognition Toggle
  const toggleListening = () => {
    if (!speechRecognitionRef.current) {
      alert('Speech recognition is supported in Google Chrome and Microsoft Edge.');
      return;
    }
    setShadowingTarget(null);
    if (isListening) {
      speechRecognitionRef.current.stop();
      setIsListening(false);
    } else {
      speechRecognitionRef.current.start();
      setIsListening(true);
    }
  };

  // Shadowing & Pronunciation Practice Mode
  const startShadowing = (targetSentence) => {
    if (!speechRecognitionRef.current) {
      alert('Speech recognition is supported in Google Chrome and Microsoft Edge.');
      return;
    }
    setShadowingTarget(targetSentence);
    setShadowResult(null);
    setIsShadowingListening(true);
    speechRecognitionRef.current.start();
  };

  const evaluateShadowing = (spoken, target) => {
    setIsShadowingListening(false);
    const cleanSpoken = spoken.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
    const cleanTarget = target.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();

    const targetWords = cleanTarget.split(/\s+/);
    const spokenWords = cleanSpoken.split(/\s+/);

    let matches = 0;
    targetWords.forEach((tw) => {
      if (spokenWords.includes(tw)) matches++;
    });

    const score = Math.min(100, Math.round((matches / targetWords.length) * 100));

    setShadowResult({
      target,
      spoken,
      score,
      feedback:
        score >= 85
          ? '🌟 Excellent pronunciation! Clear and fluent.'
          : score >= 60
          ? '👍 Good attempt! Try once more to master every sound.'
          : '💪 Keep practicing! Listen to Emma carefully and repeat slowly.'
    });

    // Update confidence stats
    setStats((prev) => ({
      ...prev,
      wordsSpoken: prev.wordsSpoken + spokenWords.length,
      sentencesCount: prev.sentencesCount + 1,
      confidenceScore: Math.min(100, Math.round((prev.confidenceScore + score) / 2))
    }));
  };

  const handleSend = async (customText = null) => {
    const textToSend = customText !== null ? customText : inputText.trim();
    if (!textToSend) return;

    if (customText === null) {
      setInputText('');
    }

    const words = textToSend.split(/\s+/).length;
    setStats((prev) => ({
      ...prev,
      wordsSpoken: prev.wordsSpoken + words,
      sentencesCount: prev.sentencesCount + 1
    }));

    const userMsgId = Date.now();
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: 'user',
        text: textToSend
      }
    ]);

    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userProfile.user_id,
          message: textToSend
        })
      });

      const data = await res.json();
      setIsTyping(false);

      if (data.type === 'interactive') {
        const interactiveButtons = (data.buttons || []).map((b) => ({
          label: b.text,
          action: () => {
            const match = b.action.match(/'([^']+)'/);
            if (match) {
              if (b.action.includes('selectLevel')) handleSend(`level:${match[1]}`);
              else if (b.action.includes('selectGoal')) handleSend(`goal:${match[1]}`);
              else if (b.action.includes('selectTopic')) handleSend(`topic:${match[1]}`);
              else handleSend(match[1]);
            }
          }
        }));

        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'bot',
            text: data.text,
            buttons: interactiveButtons
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'bot',
            text: data.text,
            mistakes: data.mistakes || [],
            vocabulary: data.vocabulary || null,
            has_corrections: data.has_corrections || false
          }
        ]);

        if (data.vocabulary) {
          fetchVocab();
        }
      }

      fetchProfile();
    } catch (err) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'bot',
          text: 'Oops! I had a little hiccup. Could you try saying that again?'
        }
      ]);
    }
  };

  const handleTranslateUzbek = async (msgId, explanationText) => {
    setLoadingTranslation((prev) => ({ ...prev, [msgId]: true }));
    try {
      const res = await fetch('/api/translate_uz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: explanationText })
      });
      const data = await res.json();
      setUzbekTranslations((prev) => ({ ...prev, [msgId]: data.translation }));
    } catch (e) {
      setUzbekTranslations((prev) => ({
        ...prev,
        [msgId]: 'Tarjimani olishda xatolik yuz berdi.'
      }));
    } finally {
      setLoadingTranslation((prev) => ({ ...prev, [msgId]: false }));
    }
  };

  const formatText = (text) => {
    if (!text) return '';
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
    return <span dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  const levelColors = {
    A1: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    A2: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    B1: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
    B2: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
    C1: 'bg-purple-500/15 text-purple-400 border-purple-500/30'
  };

  // Speaking Sentence Starters
  const sentenceStarters = [
    'I believe that...',
    'In my opinion...',
    'To be honest...',
    'Actually, I usually...',
    'Could you explain...?'
  ];

  return (
    <div className="flex h-screen w-full bg-[#0b1120] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-80 bg-[#151f32] border-r border-slate-800 flex flex-col p-5 gap-5 select-none shrink-0 hidden md:flex">
        {/* Brand Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center text-2xl shadow-lg shadow-sky-500/20">
              👩‍🏫
            </div>
            <div>
              <h1 className="font-bold text-lg text-white flex items-center gap-1.5">
                Emma
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  AI Tutor
                </span>
              </h1>
              <p className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Speaking Coach Active
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowSettingsModal(true)}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            title="Settings & API Key"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

        {/* Fluency & Confidence Score Widget */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800/80 border border-slate-700/60 rounded-2xl p-4 flex flex-col gap-3 shadow-inner">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-sky-400" />
              Speaking Confidence
            </span>
            <span className="text-xs font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded-full border border-sky-500/20">
              {stats.confidenceScore}%
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-700/50">
            <div
              className="bg-gradient-to-r from-sky-500 to-emerald-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${stats.confidenceScore}%` }}
            ></div>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1 text-center">
            <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800">
              <div className="text-[10px] text-slate-400">Words</div>
              <div className="text-sm font-bold text-white">{stats.wordsSpoken}</div>
            </div>
            <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800">
              <div className="text-[10px] text-slate-400">Sentences</div>
              <div className="text-sm font-bold text-white">{stats.sentencesCount}</div>
            </div>
            <div className="bg-slate-950/60 rounded-xl p-2 border border-slate-800">
              <div className="text-[10px] text-slate-400">Streak</div>
              <div className="text-sm font-bold text-amber-400 flex items-center justify-center gap-1">
                <Flame className="w-3 h-3 fill-amber-400" />
                {stats.streak}d
              </div>
            </div>
          </div>
        </div>

        {/* Vocabulary Bank Button (Prominent) */}
        <button
          onClick={() => {
            fetchVocab();
            setShowVocabModal(true);
          }}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 font-bold text-sm flex items-center justify-between transition-all group shadow-sm"
        >
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-4 h-4 text-amber-400" />
            <span>Vocabulary Bank</span>
          </div>
          <span className="text-xs bg-amber-500/30 px-2 py-0.5 rounded-full border border-amber-400/40 text-white font-semibold">
            {vocabList.length} words
          </span>
        </button>

        {/* Level Switcher */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              English Level
            </span>
            <span className={`text-[11px] px-2 py-0.2 rounded font-bold border ${levelColors[userProfile.level] || levelColors.B1}`}>
              {userProfile.level}
            </span>
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {['A1', 'A2', 'B1', 'B2', 'C1'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => handleSend(`level:${lvl}`)}
                className={`py-1.5 rounded-lg text-xs font-bold transition-all border ${
                  userProfile.level === lvl
                    ? 'bg-sky-500 text-slate-950 border-sky-400 shadow-md shadow-sky-500/25 scale-105'
                    : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 border-slate-700/60'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Practice Commands */}
        <div className="flex flex-col gap-2 flex-1 overflow-y-auto pr-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Speech Practice & Tools
          </span>

          <div className="grid grid-cols-1 gap-2">
            <button
              onClick={() => handleSend('/topic')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 text-slate-200 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <Lightbulb className="w-4 h-4 text-amber-400 shrink-0" />
              <span>3 Topics to Talk About</span>
            </button>

            <button
              onClick={() => handleSend('/quiz')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 text-slate-200 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <Award className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>5-Question Review Quiz</span>
            </button>

            <button
              onClick={() => handleSend('/summary')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 text-slate-200 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <BarChart2 className="w-4 h-4 text-sky-400 shrink-0" />
              <span>Mistakes & Vocab Report</span>
            </button>

            <button
              onClick={() => handleSend('/strict')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 text-slate-200 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <Flame className="w-4 h-4 text-rose-400 shrink-0" />
              <span>Strict Mode (All Errors)</span>
            </button>

            <button
              onClick={() => handleSend('/relax')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/50 text-slate-200 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <Globe className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>Relaxed Mode (Fluency)</span>
            </button>

            <button
              onClick={() => handleSend('/reset')}
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-slate-800/50 hover:bg-rose-950/40 border border-slate-700/50 hover:border-rose-800/50 text-slate-300 text-xs font-semibold transition-all hover:translate-x-1 text-left"
            >
              <RotateCcw className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Reset Chat History</span>
            </button>
          </div>
        </div>

        {/* Footer info */}
        <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${apiKeyStatus === 'configured' ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
            {apiKeyStatus === 'configured' ? 'Gemini 2.5 Flash' : 'Smart Offline Mode'}
          </span>
          <button onClick={() => setShowSettingsModal(true)} className="hover:text-sky-400 underline">
            API Key
          </button>
        </div>
      </aside>

      {/* Main Conversation Stream */}
      <main className="flex-1 flex flex-col h-screen bg-[#0b1120] relative overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="h-16 border-b border-slate-800 bg-[#151f32]/90 backdrop-blur-md px-6 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center text-lg md:hidden">
              👩‍🏫
            </div>
            <div>
              <h2 className="font-bold text-sm md:text-base text-white flex items-center gap-2">
                English Speaking & Conversation Coach
              </h2>
              <p className="text-xs text-slate-400 flex items-center gap-2">
                <span>Practicing with Emma</span>
                <span>•</span>
                <span className="text-sky-300">{userProfile.goal}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Speed Toggle for TTS */}
            <button
              onClick={() => setSpeechRate((r) => (r === 1.0 ? 0.75 : 1.0))}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                speechRate === 0.75
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}
              title="Toggle slow clear speech for beginners"
            >
              <Headphones className="w-3.5 h-3.5" />
              <span>{speechRate === 0.75 ? '🐢 Slow (0.75x)' : '🔊 Normal (1x)'}</span>
            </button>

            <button
              onClick={() => {
                fetchVocab();
                setShowVocabModal(true);
              }}
              className="flex md:hidden items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>{vocabList.length} Vocab</span>
            </button>

            <button
              onClick={() => handleSend('/help')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5 text-sky-400" />
              <span>Help</span>
            </button>
          </div>
        </header>

        {/* Shadowing Score Banner if Active */}
        {shadowResult && (
          <div className="bg-gradient-to-r from-sky-950 via-indigo-950 to-slate-900 border-b border-sky-500/30 px-6 py-3 flex items-center justify-between text-xs animate-in slide-in-from-top duration-300">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                  shadowResult.score >= 80 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                }`}
              >
                {shadowResult.score}%
              </div>
              <div>
                <div className="font-bold text-white text-sm">{shadowResult.feedback}</div>
                <div className="text-slate-400">
                  You said: <span className="text-sky-300 italic">"{shadowResult.spoken}"</span>
                </div>
              </div>
            </div>
            <button onClick={() => setShadowResult(null)} className="text-slate-400 hover:text-white p-1">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 flex flex-col gap-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}
            >
              {msg.role === 'bot' && (
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center text-sm shrink-0 shadow-md">
                  👩‍🏫
                </div>
              )}

              <div
                className={`flex flex-col gap-2 rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white rounded-tr-none'
                    : 'bg-[#151f32] border border-slate-800 text-slate-200 rounded-tl-none'
                }`}
              >
                {/* Audio Listen & Shadowing Controls on Emma's reply */}
                {msg.role === 'bot' && (
                  <div className="flex items-center justify-between pb-1 border-b border-slate-800/80 mb-1">
                    <button
                      onClick={() => speakText(msg.text, msg.id)}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                        speakingMsgId === msg.id
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse'
                          : 'bg-slate-800/80 hover:bg-slate-700 text-sky-400 border border-slate-700/60'
                      }`}
                    >
                      {speakingMsgId === msg.id ? (
                        <>
                          <VolumeX className="w-3.5 h-3.5" />
                          <span>Stop Audio</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Listen (Tinglash)</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => startShadowing(msg.text)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 transition-all"
                      title="Repeat after Emma and check your pronunciation score"
                    >
                      <Mic className="w-3.5 h-3.5" />
                      <span>Repeat & Practice</span>
                    </button>
                  </div>
                )}

                {/* Main Conversational Text */}
                <div className="text-sm md:text-[15px]">{formatText(msg.text)}</div>

                {/* Structured Correction Block */}
                {msg.mistakes && msg.mistakes.length > 0 && (
                  <div className="mt-2.5 p-3.5 rounded-xl bg-slate-950/90 border border-rose-500/25 flex flex-col gap-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        Gentle Correction
                      </div>
                      <span className="text-[11px] text-slate-400">Tap to hear correct version</span>
                    </div>

                    {msg.mistakes.map((m, idx) => (
                      <div key={idx} className="flex flex-col gap-1 text-xs">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="line-through text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                            {m.original}
                          </span>
                          <span className="text-slate-400">→</span>
                          <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            {m.corrected}
                          </span>
                          <button
                            onClick={() => speakText(m.corrected, `corr_${msg.id}_${idx}`)}
                            className="p-1 text-sky-400 hover:text-sky-300"
                            title="Listen to correct pronunciation"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="text-slate-400 flex items-start gap-1.5 mt-0.5 pl-0.5">
                          <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <span>{m.explanation}</span>
                        </div>
                      </div>
                    ))}

                    {/* Uzbek Translation Feature */}
                    <div className="mt-1 pt-2 border-t border-slate-800/80">
                      {uzbekTranslations[msg.id] ? (
                        <div className="p-2.5 rounded-lg bg-sky-950/40 border border-sky-500/30 text-xs text-sky-200 flex flex-col gap-1">
                          <span className="font-bold text-sky-300 flex items-center gap-1.5">
                            🇺🇿 O'zbekcha tushuntirish:
                          </span>
                          <span>{uzbekTranslations[msg.id]}</span>
                        </div>
                      ) : (
                        <button
                          disabled={loadingTranslation[msg.id]}
                          onClick={() =>
                            handleTranslateUzbek(
                              msg.id,
                              msg.mistakes.map((m) => m.explanation).join('. ')
                            )
                          }
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-300 text-xs font-semibold transition-colors"
                        >
                          <Globe className="w-3.5 h-3.5" />
                          {loadingTranslation[msg.id]
                            ? 'Tarjima qilinmoqda...'
                            : "🇺🇿 Explain in Uzbek / O'zbekcha tushuntirish"}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Vocabulary Card */}
                {msg.vocabulary && (
                  <div className="mt-2 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 flex flex-col gap-1.5 text-xs text-amber-200">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                        <BookOpen className="w-3.5 h-3.5" />
                        New Vocabulary Taught
                      </span>
                      <button
                        onClick={() => speakText(msg.vocabulary.phrase, `voc_${msg.id}`)}
                        className="p-1 text-amber-300 hover:text-white"
                        title="Listen to pronunciation"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="text-white font-bold text-sm">
                      "{msg.vocabulary.phrase}" ={' '}
                      <span className="text-amber-200 font-normal">{msg.vocabulary.definition}</span>
                    </div>

                    {msg.vocabulary.example && (
                      <div className="text-slate-400 italic mt-0.5">Example: {msg.vocabulary.example}</div>
                    )}
                  </div>
                )}

                {/* Interactive Suggestion / Choice Buttons */}
                {msg.buttons && msg.buttons.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-slate-800/60">
                    {msg.buttons.map((btn, i) => (
                      <button
                        key={i}
                        onClick={btn.action}
                        className="px-3.5 py-1.5 rounded-full bg-slate-800 hover:bg-sky-500 hover:text-slate-950 text-slate-200 text-xs font-medium border border-slate-700 hover:border-sky-400 transition-all shadow-sm"
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex items-center gap-3 self-start">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center text-sm shrink-0">
                👩‍🏫
              </div>
              <div className="bg-[#151f32] border border-slate-800 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-400 animate-bounce"></span>
                <span
                  className="w-2 h-2 rounded-full bg-sky-400 animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                ></span>
                <span
                  className="w-2 h-2 rounded-full bg-sky-400 animate-bounce"
                  style={{ animationDelay: '0.4s' }}
                ></span>
                <span className="text-xs text-slate-400 ml-1 font-medium">
                  Emma is thinking & analyzing speech...
                </span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Sentence Starters & Input Area */}
        <footer className="p-4 md:p-6 bg-[#151f32]/90 border-t border-slate-800/80 backdrop-blur-md flex flex-col gap-3">
          {/* Sentence Starter Helpers */}
          <div className="max-w-4xl mx-auto w-full flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-slate-400 font-semibold flex items-center gap-1 shrink-0">
              <Smile className="w-3.5 h-3.5 text-amber-400" />
              Start with:
            </span>
            {sentenceStarters.map((starter, i) => (
              <button
                key={i}
                onClick={() => setInputText((prev) => (prev ? prev + ' ' + starter : starter))}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 shrink-0 transition-colors"
              >
                {starter}
              </button>
            ))}
          </div>

          <div className="max-w-4xl mx-auto w-full flex items-center gap-3">
            <button
              onClick={toggleListening}
              title={isListening ? 'Listening... click to stop' : 'Tap to speak English into microphone'}
              className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all shrink-0 border ${
                isListening
                  ? 'bg-rose-500 text-white border-rose-400 animate-pulse'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
              }`}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-sky-400" />}
            </button>

            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
              placeholder={
                isListening
                  ? 'Listening to your voice... Speak now in English!'
                  : 'Type your message in English or use voice...'
              }
              className="flex-1 bg-slate-950 border border-slate-800 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition-all"
            />

            <button
              onClick={() => handleSend()}
              disabled={!inputText.trim()}
              className="w-11 h-11 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:opacity-40 disabled:hover:bg-sky-500 text-slate-950 font-bold flex items-center justify-center transition-all shrink-0 shadow-md shadow-sky-500/20"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </footer>
      </main>

      {/* Vocabulary Bank Modal */}
      {showVocabModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#151f32] border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <BookOpen className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-base text-white">Vocabulary Bank (Lug'at Banki)</h3>
                <span className="text-xs bg-amber-500/20 text-amber-300 px-2.5 py-0.5 rounded-full border border-amber-500/30">
                  {vocabList.length} words
                </span>
              </div>
              <button
                onClick={() => setShowVocabModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Search Input */}
            <div className="p-4 border-b border-slate-800 bg-slate-950/40">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={vocabSearch}
                  onChange={(e) => setVocabSearch(e.target.value)}
                  placeholder="Search words, definitions, or examples..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-amber-500"
                />
              </div>
            </div>

            {/* Words List */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
              {vocabList.filter(
                (v) =>
                  v.phrase.toLowerCase().includes(vocabSearch.toLowerCase()) ||
                  v.definition.toLowerCase().includes(vocabSearch.toLowerCase())
              ).length === 0 ? (
                <div className="py-12 text-center text-slate-400 text-sm flex flex-col items-center gap-2">
                  <BookOpen className="w-8 h-8 text-slate-600" />
                  <span>No vocabulary words saved yet. Chat with Emma to learn new phrases!</span>
                </div>
              ) : (
                vocabList
                  .filter(
                    (v) =>
                      v.phrase.toLowerCase().includes(vocabSearch.toLowerCase()) ||
                      v.definition.toLowerCase().includes(vocabSearch.toLowerCase())
                  )
                  .map((v, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/40 transition-all flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-white font-bold text-sm flex items-center gap-2">
                          <span>{v.phrase}</span>
                          <button
                            onClick={() => speakText(v.phrase, `vlist_${i}`)}
                            className="p-1 text-amber-400 hover:text-amber-300"
                            title="Hear pronunciation"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <span className="text-[10px] text-slate-400">{v.timestamp?.split(' ')[0]}</span>
                      </div>
                      <div className="text-amber-200/90 text-xs">{v.definition}</div>
                      {v.example && (
                        <div className="text-slate-400 text-xs italic bg-slate-950/60 p-2 rounded-lg border border-slate-850 mt-1">
                          "{v.example}"
                        </div>
                      )}
                    </div>
                  ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex justify-end">
              <button
                onClick={() => setShowVocabModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings / API Key Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#151f32] border border-slate-700 rounded-2xl w-full max-w-md p-6 flex flex-col gap-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 font-bold text-base text-white">
                <Settings className="w-5 h-5 text-sky-400" />
                <span>AI Tutor Settings</span>
              </div>
              <button onClick={() => setShowSettingsModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-bold text-slate-300">Google Gemini API Key</label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Get your free API key at{' '}
                <a
                  href="https://aistudio.google.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-sky-400 underline"
                >
                  Google AI Studio
                </a>
                .
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-slate-300">
                {apiKeyStatus === 'configured'
                  ? 'Gemini 2.5 Flash connected and active.'
                  : 'Currently in Smart Offline Coach Mode.'}
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveApiKey}
                disabled={savingKey || !apiKeyInput.trim()}
                className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:opacity-40 text-slate-950 font-bold text-xs"
              >
                {savingKey ? 'Saving...' : 'Save API Key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
