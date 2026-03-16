"use client";

import { useState, useEffect } from "react";
import {
    Activity, Globe, Copy, Download, CheckSquare,
    Square, Loader2, AlertCircle, FileText, CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.optimiseurbrand.tech";

const AVAILABLE_SKILLS = [
    { id: "technical", label: "Technical SEO", description: "Core Web Vitals, Crawlability, Meta tags" },
    { id: "content", label: "Content Quality", description: "E-E-A-T, Readability, Keyword optimization" },
    { id: "schema", label: "Schema Markup", description: "JSON-LD validation and recommendations" },
    { id: "performance", label: "Performance", description: "LCP, INP, CLS diagnostics" },
    { id: "sitemap", label: "Sitemap", description: "Architecture and Quality Gates" }
];

export function SeoAnalyzer() {
    const [url, setUrl] = useState("");
    const [selectedSkills, setSelectedSkills] = useState<string[]>(["technical"]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<any>(null);

    const [toolUsage, setToolUsage] = useState<any>(null);

    useEffect(() => {
        fetchToolUsage();
    }, []);

    const fetchToolUsage = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const res = await fetch(`${API_BASE_URL}/api/tools/usage`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setToolUsage(data.usage);

                // Prevent used skills from being selected by default
                if (data.usage?.seo_skills) {
                    setSelectedSkills(prev => prev.filter(skillId => !data.usage.seo_skills[skillId] || data.usage.seo_skills[skillId] < 1).slice(0, 1));
                }
            }
        } catch (e) {
            console.error("Failed to fetch tool usage", e);
        }
    };

    const toggleSkill = (skillId: string) => {
        if (toolUsage?.seo_skills?.[skillId] >= 1) return; // limit reached
        setSelectedSkills(prev =>
            prev.includes(skillId)
                ? []
                : [skillId]
        );
    };

    const handleAnalyze = async () => {
        if (!url) {
            setError("Please enter a valid URL.");
            return;
        }
        if (selectedSkills.length === 0) {
            setError("Please select at least one SEO skill to evaluate.");
            return;
        }

        let formatUrl = url.trim();
        if (!formatUrl.startsWith("http")) formatUrl = "https://" + formatUrl;

        setIsGenerating(true);
        setError(null);
        setResults(null);

        try {
            const token = localStorage.getItem('token');
            const headers: Record<string, string> = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}/api/seo/analyze`, {
                method: "POST",
                headers,
                body: JSON.stringify({
                    url: formatUrl,
                    skills: selectedSkills
                }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Failed to analyze URL");
            }

            const data = await response.json();
            setResults(data.data);
            fetchToolUsage(); // Update usage after successful analysis

        } catch (err: any) {
            setError(err.message || "An unexpected error occurred.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopy = (content: string) => {
        navigator.clipboard.writeText(content);
        // Could add a toast here
    };

    const handleDownload = (content: string, filename: string) => {
        const blob = new Blob([content], { type: "text/markdown" });
        const objUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = objUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objUrl);
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500 max-w-5xl mx-auto p-6">
            {/* Hero Header */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-teal-500 to-emerald-500 px-8 py-10">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djZoLTZWMzRoNnptMC0zMHY2aC02VjRoNnptMCAxMnY2aC02VjE2aDZ6bTAgMTJ2Nmg2djZoNnYtNmgtNnYtNmgtNnptMTIgMTJ2Nmg2di02aC02em0xMi0xMnY2aDZ2LTZoLTZ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30" />
                <div className="relative">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-sm text-white/90 text-xs font-medium">
                            <Activity className="h-3.5 w-3.5" />
                            Free Tool
                        </div>
                    </div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
                        SEO Analyzer
                    </h1>
                    <p className="text-white/80 text-sm max-w-xl leading-relaxed">
                        Analyze any website natively using Claude SEO specialist agents. Follows Google's Quality Rater Guidelines and Core Web Vitals targets.
                    </p>
                </div>
            </div>

            {/* URL Input Card */}
            <div className="dashboard-card p-6 bg-white rounded-xl border border-gray-200">
                <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                        Website URL
                    </label>
                    <div className="relative">
                        <Globe className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-gray-400" />
                        <input
                            type="text"
                            className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all disabled:opacity-50"
                            placeholder="https://example.com"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                        />
                    </div>
                </div>

                <div className="mb-8">
                    <div className="flex items-center justify-between mb-3">
                        <label className="block text-sm font-semibold text-gray-700">
                            Select Analytical Skill
                        </label>
                        <span className="text-xs text-teal-600 bg-teal-50 px-2 py-1 rounded-full font-medium border border-teal-100">
                            Please select 1 skill (1 use per skill)
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {AVAILABLE_SKILLS.map((skill) => {
                            const isSelected = selectedSkills.includes(skill.id);
                            const isUsed = toolUsage?.seo_skills?.[skill.id] >= 1;

                            return (
                                <div
                                    key={skill.id}
                                    onClick={() => !isUsed && toggleSkill(skill.id)}
                                    className={`p-4 rounded-xl border transition-all ${isUsed
                                        ? "bg-gray-100 border-gray-200 opacity-60 cursor-not-allowed"
                                        : isSelected
                                            ? "bg-teal-50 border-teal-200 text-teal-900 shadow-sm cursor-pointer"
                                            : "bg-gray-50 border-gray-200 text-gray-600 hover:border-teal-300 hover:bg-white cursor-pointer"
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-sm">{skill.label}</span>
                                            {isUsed && (
                                                <span className="text-[10px] uppercase font-bold text-gray-400 border border-gray-300 px-1.5 py-0.5 rounded">
                                                    Used
                                                </span>
                                            )}
                                        </div>
                                        {isSelected ? <CheckSquare className="w-4 h-4 text-teal-600" /> : <Square className="w-4 h-4 text-gray-400" />}
                                    </div>
                                    <p className={`text-xs ${isSelected ? 'text-teal-700/80' : 'text-gray-500'}`}>{skill.description}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-500" />
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                )}

                <div className="flex items-center gap-4">
                    <Button
                        className="px-6 py-3 rounded-xl bg-teal-500 hover:bg-teal-600 text-white font-semibold h-auto shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30 transition-all disabled:opacity-50 disabled:shadow-none"
                        onClick={handleAnalyze}
                        disabled={isGenerating || !url}
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Analyzing (Crawling up to 30 pages)...
                            </>
                        ) : (
                            "Run SEO Analysis"
                        )}
                    </Button>
                </div>
            </div>

            {/* Results Section */}
            {results && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-6 duration-500">
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 text-teal-600 mb-2">
                            <CheckCircle2 className="w-5 h-5" />
                            <span className="font-medium">Analysis Complete</span>
                        </div>
                        <p className="text-sm text-gray-500">
                            Crawled {results.pages_crawled} pages on {results.url}
                        </p>
                    </div>

                    {Object.entries(results.results).map(([skill, content]) => (
                        <div key={skill} className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/80">
                                <div className="flex items-center gap-2">
                                    <FileText className="w-5 h-5 text-teal-500" />
                                    <h2 className="text-md font-semibold text-gray-900 capitalize">{skill} Analysis</h2>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        onClick={() => handleCopy(content as string)}
                                        variant="outline" size="sm"
                                        className="text-xs border-gray-200 hover:bg-gray-100 rounded-lg text-gray-600"
                                        title="Copy markdown"
                                    >
                                        <Copy className="w-3.5 h-3.5 mr-1.5" /> Copy
                                    </Button>
                                    <Button
                                        onClick={() => handleDownload(content as string, `${skill}_analysis.md`)}
                                        variant="outline" size="sm"
                                        className="text-xs border-gray-200 hover:bg-gray-100 rounded-lg text-gray-600"
                                        title="Download as .md"
                                    >
                                        <Download className="w-3.5 h-3.5 mr-1.5" /> Download
                                    </Button>
                                </div>
                            </div>
                            <div className="p-6 bg-gray-50/50 overflow-x-auto">
                                <pre className="text-gray-700 text-sm font-mono whitespace-pre-wrap leading-relaxed shadow-inner bg-white border border-gray-200 p-4 rounded-xl">
                                    {content as string}
                                </pre>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
