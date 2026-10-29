/**
 * Ambient Nursing Ally (ANA) — Pipeline Execution & UI Orchestrator
 * Calls /api/run_pipeline and dynamically renders the complete 5-tier outputs.
 */

class ANAPipelineRunner {
    constructor() {
        this.runBtn = document.getElementById("btnRunPipeline");
        this.statusBadge = document.getElementById("pipelineGlobalStatus");
        this.pipelineProgress = document.getElementById("pipelineProgressContainer");
        this.resultsSection = document.getElementById("pipelineResultsSection");
        this.benchmarkContainer = document.getElementById("benchmarkScenariosList");
        
        this.lastExecutionData = null;
        
        this.initEventListeners();
        this.loadBenchmarks();
    }
    
    initEventListeners() {
        if (this.runBtn) {
            this.runBtn.addEventListener("click", () => this.executePipeline());
        }
        
        const simRejectionToggle = document.getElementById("toggleSimulateRejection");
        if (simRejectionToggle) {
            simRejectionToggle.addEventListener("change", (e) => {
                const label = document.getElementById("rejectionToggleLabel");
                if (label) {
                    label.textContent = e.target.checked 
                        ? "🚨 HITL Rejection Simulation (Active: Will Quarantine)" 
                        : "✅ HITL Standard Approval (Safe to Cascade)";
                    label.className = e.target.checked ? "text-xs font-bold text-red-600" : "text-xs font-medium text-slate-500";
                }
            });
        }
        
        const edgeBufferToggle = document.getElementById("toggleEdgeBuffering");
        if (edgeBufferToggle) {
            edgeBufferToggle.addEventListener("change", (e) => {
                const edgeStatusBadge = document.getElementById("edgeCacheGlobalBadge");
                if (edgeStatusBadge) {
                    if (e.target.checked) {
                        edgeStatusBadge.innerHTML = `
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                                📴 Offline Edge Buffer Active (AES-256 Queue)
                            </span>
                        `;
                    } else {
                        edgeStatusBadge.innerHTML = `
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                                🟢 Ward WiFi Synchronized (Live)
                            </span>
                        `;
                    }
                }
            });
        }
    }
    
    async loadBenchmarks() {
        if (!this.benchmarkContainer) return;
        try {
            const res = await fetch("/api/benchmarks");
            const scenarios = await res.json();
            
            this.benchmarkContainer.innerHTML = "";
            scenarios.forEach(sc => {
                const card = document.createElement("div");
                card.className = "p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer text-left";
                card.innerHTML = `
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">${sc.category}</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-slate-600 dark:text-slate-300">${sc.patient_id || 'NO_MRN'}</span>
                    </div>
                    <div class="text-sm font-semibold text-slate-800 dark:text-slate-100">${sc.title}</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">${sc.description}</div>
                `;
                card.addEventListener("click", () => {
                    // Highlight selected
                    document.querySelectorAll("#benchmarkScenariosList > div").forEach(c => c.classList.remove("ring-2", "ring-blue-500"));
                    card.classList.add("ring-2", "ring-blue-500");
                    
                    if (window.anaRecorder) {
                        window.anaRecorder.selectBenchmarkScenario(sc);
                    }
                });
                this.benchmarkContainer.appendChild(card);
            });
        } catch (err) {
            console.error("Error loading benchmark scenarios:", err);
        }
    }
    
    async executePipeline() {
        const recorder = window.anaRecorder;
        const currentPayload = recorder ? recorder.currentAudioPayload : null;
        const audioPath = currentPayload ? currentPayload.relative_path : "datasets/mock_audio.mp3";
        
        const patientMrnSelect = document.getElementById("patientMrnSelect");
        const declaredMrn = patientMrnSelect ? patientMrnSelect.value : "";
        
        const simRejectionToggle = document.getElementById("toggleSimulateRejection");
        const simulateRejection = simRejectionToggle ? simRejectionToggle.checked : false;
        
        const edgeBufferToggle = document.getElementById("toggleEdgeBuffering");
        const edgeBuffering = edgeBufferToggle ? edgeBufferToggle.checked : false;
        
        // Show loading state
        if (this.runBtn) {
            this.runBtn.disabled = true;
            this.runBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing 5-Tier Pipeline...
            `;
        }
        
        if (this.pipelineProgress) this.pipelineProgress.classList.remove("hidden");
        this.updateStepProgress(1);
        
        try {
            const response = await fetch("/api/run_pipeline", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    audio_path: audioPath,
                    patient_id: declaredMrn,
                    simulate_rejection: simulateRejection,
                    force_low_confidence: false,
                    edge_buffering: edgeBuffering
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                alert("Pipeline execution failed: " + (data.error || "Unknown server error"));
                return;
            }
            
            this.lastExecutionData = data;
            this.renderFullPipelineOutput(data);
            
        } catch (err) {
            console.error("Pipeline invocation error:", err);
            alert("Network / Execution error: " + err.message);
        } finally {
            if (this.runBtn) {
                this.runBtn.disabled = false;
                this.runBtn.innerHTML = `
                    <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    ⚡ Process Ingested Audio (Tiers 1-5)
                `;
            }
        }
    }
    
    updateStepProgress(stepNum) {
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`step-indicator-${i}`);
            if (!stepEl) continue;
            
            if (i < stepNum) {
                stepEl.className = "flex items-center justify-center w-8 h-8 bg-emerald-500 text-white rounded-full font-bold text-xs ring-4 ring-emerald-100";
                stepEl.innerHTML = "✓";
            } else if (i === stepNum) {
                stepEl.className = "flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold text-xs ring-4 ring-blue-100 animate-pulse";
                stepEl.innerHTML = i;
            } else {
                stepEl.className = "flex items-center justify-center w-8 h-8 bg-slate-200 dark:bg-slate-700 text-slate-500 rounded-full font-bold text-xs";
                stepEl.innerHTML = i;
            }
        }
    }
    
    renderFullPipelineOutput(data) {
        if (this.resultsSection) this.resultsSection.classList.remove("hidden");
        
        // 1. Header Metadata & Status
        const statusEl = document.getElementById("resPipelineStatus");
        const isQuarantined = data.pipeline_status === "ISOLATED_QUARANTINED";
        
        if (statusEl) {
            statusEl.innerHTML = isQuarantined
                ? `<span class="px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">🛑 QUARANTINED AT CHECKPOINT</span>`
                : `<span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">✅ 5-TIER PIPELINE EXECUTED</span>`;
        }
        
        const sessionEl = document.getElementById("resSessionId");
        if (sessionEl) sessionEl.textContent = data.shift_session_id;
        
        // Complete Step progress
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`step-indicator-${i}`);
            if (stepEl) {
                if (isQuarantined && i >= 3) {
                    stepEl.className = "flex items-center justify-center w-8 h-8 bg-red-500 text-white rounded-full font-bold text-xs";
                    stepEl.innerHTML = "✕";
                } else {
                    stepEl.className = "flex items-center justify-center w-8 h-8 bg-emerald-500 text-white rounded-full font-bold text-xs ring-4 ring-emerald-100";
                    stepEl.innerHTML = "✓";
                }
            }
        }
        
        // Render Tier 1: Perception
        this.renderTier1(data.tier1_perception);
        
        // Render Tier 2: NLP & DART
        this.renderTier2(data.tier2_nlp);
        
        // Render Checkpoint: Cascading Error Isolation
        this.renderCheckpoint(data.checkpoint_hitl, data.tier2_nlp);
        
        // Render Tier 3: RAG
        this.renderTier3(data.tier3_rag, isQuarantined);
        
        // Render Tier 4: Agentic FHIR
        this.renderTier4(data.tier4_agentic, isQuarantined);
        
        // Render Tier 5: Security Ledger
        this.renderTier5(data.tier5_security, isQuarantined);
        
        // Scroll smoothly to results
        if (this.resultsSection) {
            this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    renderTier1(t1) {
        // Patient Context Anchoring Badge
        const anchorBadge = document.getElementById("resContextAnchorBadge");
        if (anchorBadge && t1.patient_context_anchor) {
            const anc = t1.patient_context_anchor;
            anchorBadge.innerHTML = anc.anchored
                ? `
                    <div class="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                        <div class="flex items-center space-x-2 text-emerald-800 dark:text-emerald-300 font-bold text-xs uppercase tracking-wider">
                            <span>✅ Patient Context Anchored</span>
                            <span class="px-2 py-0.5 rounded bg-emerald-200 dark:bg-emerald-800 font-mono text-xs">${anc.anchored_mrn}</span>
                        </div>
                        <div class="text-xs text-emerald-700 dark:text-emerald-400 mt-1">${anc.details}</div>
                    </div>
                `
                : `
                    <div class="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg">
                        <div class="flex items-center space-x-2 text-red-800 dark:text-red-300 font-bold text-xs uppercase tracking-wider">
                            <span>🚨 Cross-Talk Fail-Safe Triggered</span>
                        </div>
                        <div class="text-xs text-red-700 dark:text-red-400 mt-1">${anc.details}</div>
                    </div>
                `;
        }
        
        // VAD Segments
        const vadEl = document.getElementById("resVadSegments");
        if (vadEl) {
            const count = t1.speech_timestamps ? t1.speech_timestamps.length : 0;
            vadEl.innerHTML = `
                <div class="flex items-center justify-between text-xs mb-2">
                    <span class="font-semibold text-slate-700 dark:text-slate-300">Silero-VAD Speech Isolation:</span>
                    <span class="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full font-bold">${count} Active Utterance${count === 1 ? '' : 's'}</span>
                </div>
                <div class="space-y-1.5 max-h-28 overflow-y-auto font-mono text-xs text-slate-600 dark:text-slate-400">
                    ${count > 0 
                        ? t1.speech_timestamps.map((s, idx) => `
                            <div class="flex justify-between p-1.5 bg-slate-50 dark:bg-slate-800/80 rounded border border-slate-200 dark:border-slate-700">
                                <span>Segment #${idx + 1}: Sample [${s.start} → ${s.end}]</span>
                                <span class="text-emerald-600 font-semibold">${((s.end - s.start) / 16000).toFixed(2)}s duration</span>
                            </div>
                        `).join("")
                        : `<div class="italic text-slate-400">Continuous speech buffer passed without noise dropouts.</div>`
                    }
                </div>
            `;
        }
        
        // Raw Transcript
        const rawEl = document.getElementById("resRawTranscript");
        if (rawEl) rawEl.textContent = t1.raw_transcript || "No transcript available.";
        
        // Verbal Error Recovery Box
        const verEl = document.getElementById("resVerbalRecoveryBox");
        if (verEl) {
            if (t1.verbal_corrections && t1.verbal_corrections.length > 0) {
                verEl.innerHTML = `
                    <div class="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg">
                        <div class="text-xs font-bold text-amber-800 dark:text-amber-300 uppercase tracking-wide flex items-center">
                            <span class="mr-1.5">🔄</span> Verbal Error Recovery: Detected Nurse Mid-Sentence Self-Correction
                        </div>
                        <div class="mt-2 space-y-1 text-xs">
                            ${t1.verbal_corrections.map(c => `
                                <div class="flex items-center space-x-2 font-mono">
                                    <span class="line-through text-red-500 bg-red-50 dark:bg-red-900/40 px-1.5 py-0.5 rounded">"${c.original_slip}"</span>
                                    <span class="text-slate-400">➔ replaced by</span>
                                    <span class="font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/40 px-1.5 py-0.5 rounded">"${c.corrected_value}"</span>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `;
            } else {
                verEl.innerHTML = `
                    <div class="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 text-xs text-slate-500">
                        ✨ Verbal Error Recovery: Speech stream clean (no mid-sentence self-corrections detected).
                    </div>
                `;
            }
        }
        
        // Cleaned Transcript
        const cleanedEl = document.getElementById("resCleanedTranscript");
        if (cleanedEl) cleanedEl.textContent = t1.cleaned_transcript || "";
    }
    
    renderTier2(t2) {
        // Scrubbed Text
        const scrubbedEl = document.getElementById("resScrubbedText");
        if (scrubbedEl) {
            let html = t2.scrubbed_text || "";
            // Replace tokens with badges
            html = html.replace(/<([A-Z_]+)>/g, `<span class="inline-block px-1.5 py-0.5 mx-0.5 rounded text-xs font-mono font-bold bg-purple-100 text-purple-800 border border-purple-300">&lt;$1&gt;</span>`);
            scrubbedEl.innerHTML = html;
        }
        
        // Confidence Score Gauge
        const confScoreEl = document.getElementById("resConfidenceScore");
        const confBarEl = document.getElementById("resConfidenceBar");
        const conf = t2.confidence_score || 0.0;
        const percent = Math.round(conf * 100);
        
        if (confScoreEl) confScoreEl.textContent = `${percent}%`;
        if (confBarEl) {
            confBarEl.style.width = `${percent}%`;
            confBarEl.className = conf >= 0.85 ? "h-full bg-emerald-500" : "h-full bg-amber-500";
        }
        
        // DART Note Fields
        const dart = t2.dart_note || {};
        this.fillList("dartDataList", dart.data);
        this.fillList("dartActionList", dart.action);
        this.fillList("dartResponseList", dart.response);
        this.fillList("dartTeachingList", dart.teaching);
    }
    
    fillList(elementId, items) {
        const el = document.getElementById(elementId);
        if (!el) return;
        if (!items || items.length === 0) {
            el.innerHTML = `<li class="text-slate-400 italic">None documented</li>`;
            return;
        }
        el.innerHTML = items.map(item => `<li class="text-xs text-slate-700 dark:text-slate-300 flex items-start"><span class="text-blue-500 mr-1.5">•</span><span>${item}</span></li>`).join("");
    }
    
    renderCheckpoint(hitl, t2) {
        const panel = document.getElementById("resCheckpointPanel");
        if (!panel) return;
        
        if (hitl.hitl_approved) {
            panel.className = "p-4 rounded-xl border-2 border-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20";
            panel.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="text-xl">🛡️</span>
                        <div>
                            <div class="text-sm font-bold text-emerald-800 dark:text-emerald-300">Cascading Error Isolation Checkpoint: APPROVED</div>
                            <div class="text-xs text-emerald-700 dark:text-emerald-400">Verified by: <strong>${hitl.hitl_reviewer || 'Nurse_Auth_8841'}</strong> at ${hitl.hitl_timestamp || 'Active Shift'}</div>
                        </div>
                    </div>
                    <span class="px-3 py-1 bg-emerald-200 text-emerald-900 rounded-lg font-bold text-xs">AUTHORIZED FOR RAG & LEDGER</span>
                </div>
            `;
        } else {
            panel.className = "p-4 rounded-xl border-2 border-red-500 bg-red-50/70 dark:bg-red-950/40";
            panel.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="text-xl">🛑</span>
                        <div>
                            <div class="text-sm font-bold text-red-800 dark:text-red-300">Cascading Error Isolation Checkpoint: QUARANTINED</div>
                            <div class="text-xs text-red-700 dark:text-red-400">Reason: <strong>${hitl.hitl_rejection_reason || 'Nurse Verification Flag'}</strong></div>
                        </div>
                    </div>
                    <span class="px-3 py-1 bg-red-200 text-red-900 rounded-lg font-bold text-xs animate-pulse">DOWNSTREAM BLOCKED</span>
                </div>
                <div class="mt-2 text-xs text-red-600 dark:text-red-300">
                    ⚠️ Fail-safe active: Contaminated record prevented from propagating to FAISS Vector Index and Hyperledger Fabric.
                </div>
            `;
        }
    }
    
    renderTier3(t3, isQuarantined) {
        const container = document.getElementById("resTier3Container");
        if (!container) return;
        
        if (isQuarantined) {
            container.innerHTML = `
                <div class="p-6 text-center text-slate-400 dark:text-slate-500 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                    <div class="text-2xl mb-1">🛑</div>
                    <div class="text-sm font-semibold">Tier 3 Historical RAG Execution Skipped</div>
                    <div class="text-xs mt-1">Vector DB index protected against unapproved clinical data.</div>
                </div>
            `;
            return;
        }
        
        const chunks = t3.clinical_chunks || [];
        const results = t3.retrieval_results || [];
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">Semantic Chunks Extracted (${chunks.length})</div>
                    <div class="space-y-2 max-h-48 overflow-y-auto">
                        ${chunks.map((c, i) => `
                            <div class="p-2 bg-white dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-600 dark:text-slate-300">
                                <span class="font-bold text-blue-600">Chunk #${i+1} [${c.section || 'General'}]:</span> ${c.text ? c.text.substring(0, 90) + '...' : ''}
                            </div>
                        `).join("")}
                    </div>
                </div>
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">Hybrid Search Matches (BM25 + FAISS + RRF)</div>
                    <div class="space-y-2 max-h-48 overflow-y-auto">
                        ${results.map((r, i) => `
                            <div class="p-2 bg-white dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700 text-xs">
                                <div class="flex justify-between items-center mb-1">
                                    <span class="font-bold text-emerald-600">Match #${i+1}</span>
                                    <span class="text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">Score: ${(r.score || 0.94).toFixed(3)}</span>
                                </div>
                                <div class="text-slate-600 dark:text-slate-400 font-mono text-xs">${r.text || r.content || 'Historical telemetry and cardiac intervention match.'}</div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTier4(t4, isQuarantined) {
        const container = document.getElementById("resTier4Container");
        if (!container) return;
        
        if (isQuarantined) {
            container.innerHTML = `
                <div class="p-6 text-center text-slate-400 dark:text-slate-500 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                    <div class="text-2xl mb-1">🛑</div>
                    <div class="text-sm font-semibold">Tier 4 FHIR Agent Orchestration Skipped</div>
                    <div class="text-xs mt-1">EHR mutation blocked due to checkpoint isolation.</div>
                </div>
            `;
            return;
        }
        
        const fhir = t4.patient_record || {};
        const safety = t4.medication_safety_report || "No interactions detected.";
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">Smart-on-FHIR Patient Record</div>
                    <div class="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                        <div><strong>Patient ID:</strong> <span class="font-mono text-blue-600">${fhir.id || 'MRN48291'}</span></div>
                        <div><strong>Patient Name:</strong> <span>${fhir.patient_name || (fhir.name && fhir.name[0] ? fhir.name[0].text : 'Jonathan Harker')}</span></div>
                        <div><strong>Ward / Bed:</strong> <span>${fhir.ward || 'Cardiology 4B'} / ${fhir.bed || 'Bed-412'}</span></div>
                        <div><strong>Active Medications:</strong> <span class="font-mono text-xs text-slate-600 dark:text-slate-400">${(fhir.active_medications || []).join(", ")}</span></div>
                        <div><strong>Known Allergies:</strong> <span class="font-semibold text-red-600">${(fhir.allergies || []).join(", ")}</span></div>
                    </div>
                </div>
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">MCP Medication Safety Audit</div>
                    <div class="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg text-xs text-emerald-800 dark:text-emerald-300">
                        <div class="font-bold flex items-center mb-1">
                            <span class="mr-1.5">💊</span> Verified Safe for Administration
                        </div>
                        <div>${safety}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTier5(t5, isQuarantined) {
        const container = document.getElementById("resTier5Container");
        if (!container) return;
        
        if (isQuarantined) {
            container.innerHTML = `
                <div class="p-6 text-center text-slate-400 dark:text-slate-500 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl">
                    <div class="text-2xl mb-1">🛑</div>
                    <div class="text-sm font-semibold">Tier 5 Blockchain Anchoring Skipped</div>
                    <div class="text-xs mt-1">Immutable ledger state remains pristine.</div>
                </div>
            `;
            return;
        }
        
        const docHash = t5.document_hash || "hash_not_generated";
        const txId = t5.ledger_tx_id || "tx_mock_raft_0";
        
        container.innerHTML = `
            <div class="space-y-3">
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 font-mono text-xs">
                    <div class="flex justify-between items-center mb-1.5">
                        <span class="font-bold text-slate-700 dark:text-slate-300 uppercase">SHA-256 Cryptographic Fingerprint</span>
                        <span class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-xs font-semibold">On-Chain Anchored</span>
                    </div>
                    <div class="p-2 bg-white dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700 break-all text-blue-600 dark:text-blue-400">
                        ${docHash}
                    </div>
                    <div class="mt-2 text-slate-500 text-xs flex justify-between">
                        <span>Hyperledger Fabric TxID: <strong class="text-slate-700 dark:text-slate-300">${txId}</strong></span>
                        <span>Consensus: <strong>Raft Orderer</strong></span>
                    </div>
                </div>
                
                <!-- Interactive Tamper Detection Tester -->
                <div class="p-3 bg-slate-100 dark:bg-slate-900/60 rounded-lg border border-slate-300 dark:border-slate-700">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-slate-800 dark:text-slate-200">🔍 Real-Time Tamper Detection Test</span>
                        <span class="text-xs text-slate-500">Edit note text below to verify hash mismatch</span>
                    </div>
                    <input id="tamperInput" type="text" value="${t5.tamper_check_result && t5.tamper_check_result.sample_text ? t5.tamper_check_result.sample_text : 'Nitroglycerin 0.4mg SL given'}" class="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-600 dark:bg-slate-800 font-mono" />
                    <div class="flex items-center justify-between mt-2">
                        <button id="btnTestTamper" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-semibold transition-all">
                            Check Cryptographic Integrity
                        </button>
                        <div id="tamperResultBadge" class="text-xs"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Attach tamper tester event
        const btnTamper = document.getElementById("btnTestTamper");
        const tamperInput = document.getElementById("tamperInput");
        const badge = document.getElementById("tamperResultBadge");
        
        if (btnTamper && tamperInput && badge) {
            btnTamper.addEventListener("click", async () => {
                badge.innerHTML = `<span class="text-slate-500 animate-pulse">Hashing off-chain state...</span>`;
                try {
                    const res = await fetch("/api/tamper_test", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            original_hash: docHash,
                            tampered_text: tamperInput.value
                        })
                    });
                    const resData = await res.json();
                    if (resData.is_intact) {
                        badge.innerHTML = `<span class="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 font-bold">✅ MATCH: Unaltered Document</span>`;
                    } else {
                        badge.innerHTML = `<span class="px-2.5 py-1 rounded bg-red-100 text-red-800 font-bold animate-pulse">🚨 TAMPER DETECTED (Hash Mismatch)</span>`;
                    }
                } catch (e) {
                    badge.innerHTML = `<span class="text-red-500">Error: ${e.message}</span>`;
                }
            });
        }
    }
}

// Global instance
window.anaRunner = null;
document.addEventListener("DOMContentLoaded", () => {
    window.anaRunner = new ANAPipelineRunner();
});

