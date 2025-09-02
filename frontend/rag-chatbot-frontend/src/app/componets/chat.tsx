"use client";
import { useState, useRef, useEffect } from "react";
import axios from "axios";
import Image from 'next/image';
import styles from '../chat.module.css';

type Message = {
    role: string;
    text: string;
    sources?: string[];
    timestamp?: Date;
};

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const newMessage: Message = { 
            role: "user", 
            text: input,
            timestamp: new Date()
        };
        setMessages((prev) => [...prev, newMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const res = await axios.post("http://localhost:5000/query", {
                query: input,
            });

            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text: res.data.answer,
                    // sources: res.data.sources.map((s: any) => 
                    //     typeof s === "object" ? s.source : s
                    // ),
                    timestamp: new Date()
                },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { 
                    role: "bot", 
                    text: "⚠️ Sorry, I encountered an error while processing your request. Please try again.",
                    timestamp: new Date()
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gradient-to-b from-[#f8faff] to-white">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#6366f1] to-[#7c3aed] shadow-lg py-4 px-6">
                <div className="max-w-5xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center">
                            <Image src="/globe.svg" alt="Nova AI" width={24} height={24} className="filter brightness-0 invert" />
                        </div>
                        <h1 className="text-2xl font-semibold text-white">
                            Kyndryl AI Assistant
                        </h1>
                    </div>
                </div>
            </div>

            {/* Chat Container */}
            <div className="flex-1 overflow-hidden">
                <div className="max-w-4xl h-full mx-auto flex flex-col">
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-6">
                        {messages.length === 0 && (
                            <div className="text-center mt-20">
                                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[#6366f1] bg-opacity-10 flex items-center justify-center">
                                    <Image src="/globe.svg" alt="Welcome" width={32} height={32} className="opacity-70" />
                                </div>
                                <p className="text-xl font-medium text-[#6366f1]">Welcome to KYNDRYL AI!</p>
                                <p className="text-sm text-gray-600 mt-2">I'm here to help you explore your documents.</p>
                            </div>
                        )}
                        
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex animate-fadeIn ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div className={`flex max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"} items-end space-x-2`}>
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform duration-200 hover:scale-110 ${
                                        msg.role === "user" ? 
                                        `${styles['avatar-user']} ml-2` : 
                                        `${styles['avatar-ai']} mr-2 border border-gray-100`
                                    }`}>
                                            {msg.role === "user" ? 
                                                <Image src="/user1.png" alt="User" width={32} height={32} /> : 
                                                <Image src="/ai.png" alt="AI Agent" width={32} height={32} />
                                            }
                                    </div>
                                    <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                                        <div
                                            className={`px-4 py-3 rounded-2xl transition-all duration-200 ${
                                                msg.role === "user"
                                                    ? "bg-[#6366f1] text-white"
                                                    : "bg-white shadow-lg hover:shadow-xl text-gray-800"
                                            }`}
                                        >
                                            <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                                            {msg.sources && msg.sources.length > 0 && (
                                                <div className={`mt-3 pt-3 border-t ${msg.role === "user" ? "border-white/20" : "border-gray-100"}`}>
                                                    <p className={`text-sm mb-2 ${msg.role === "user" ? "text-white/70" : "text-gray-500"}`}>Sources:</p>
                                                    <div className="space-y-1">
                                                        {msg.sources.map((src, i) => (
                                                            <a
                                                                key={i}
                                                                href={src}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className={`block text-sm hover:underline transition-colors ${
                                                                    msg.role === "user" 
                                                                        ? "text-white/90 hover:text-white" 
                                                                        : "text-[#6366f1] hover:text-[#4f46e5]"
                                                                }`}
                                                            >
                                                                {src}
                                                            </a>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        {msg.timestamp && (
                                            <span className="text-xs text-gray-400 mt-1">
                                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start animate-fadeIn">
                                <div className="flex items-center space-x-2 bg-white rounded-2xl shadow-lg px-4 py-3">
                                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse"></div>
                                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2 h-2 bg-[#6366f1] rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-6 bg-white border-t border-gray-100">
                        <div className="max-w-5xl mx-auto">
                            <div className={`flex items-end gap-3 p-4 rounded-2xl bg-gray-50/50 border border-gray-100 ${styles['input-glow']}`}>
                                <div className="flex-1 flex items-center">
                                    <textarea
                                        className="w-full px-4 py-3 rounded-xl bg-white border border-gray-200 focus:border-[#6366f1] focus:ring-2 focus:ring-[#6366f1]/20 transition-all duration-200 outline-none resize-none shadow-sm"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={handleKeyPress}
                                        placeholder="Ask me anything..."
                                        rows={1}
                                        style={{ minHeight: '52px', maxHeight: '150px' }}
                                    />
                                </div>
                                <button
                                    className={`p-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center min-w-[100px] h-[52px] ${
                                        input.trim() && !isLoading
                                            ? 'bg-gradient-to-r from-[#6366f1] to-[#7c3aed] hover:opacity-90 text-white shadow-lg hover:shadow-[#6366f1]/25'
                                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    }`}
                                    onClick={sendMessage}
                                    disabled={!input.trim() || isLoading}
                                >
                                    {isLoading ? (
                                        <div className="flex items-center space-x-2">
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            <span>Sending</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center space-x-2">
                                            <span>Send</span>
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                            </svg>
                                        </div>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
