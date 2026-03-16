"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnalysisProgress } from "@/components/analysis-progress";
import { CohortPromptSelector } from "@/components/cohort-prompt-selector";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

import { Header } from "@/components/header";

export default function ResultsPage() {
    const params = useParams();
    const sessionId = params.sessionId as string;
    const router = useRouter();
    const { isAuthenticated, logout } = useAuth();

    const [showPromptSelection, setShowPromptSelection] = useState(false);

    const handleResultsReady = (sessionId: string) => {
        router.push("/dashboard");
    };

    const handlePromptSelectionReady = () => {
        setShowPromptSelection(true);
    };

    const handleExecuteWizardPrompts = () => {
        setShowPromptSelection(false);
    };

    if (!isAuthenticated) return null;

    return (
        <div className="min-h-screen bg-gray-50/50">
            <Header />
            <main className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-500">
                {showPromptSelection ? (
                    <CohortPromptSelector
                        sessionId={sessionId}
                        onExecute={handleExecuteWizardPrompts}
                    />
                ) : (
                    <AnalysisProgress
                        sessionId={sessionId}
                        onComplete={handleResultsReady}
                        onPromptSelectionReady={handlePromptSelectionReady}
                    />
                )}
            </main>
        </div>
    );
}
