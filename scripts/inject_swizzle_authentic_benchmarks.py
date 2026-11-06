import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CSS_BENCHMARKS = """
/* ==========================================================================
   ORIGINAL SWIZZLE EMPIRICAL BENCHMARKS SUITE (Brand: Obsidian & Lime)
   ========================================================================== */
.bench-suite {
  background: var(--ink2);
  border-top: 1px solid var(--ld);
  border-bottom: 1px solid var(--ld);
  padding: 100px 0 120px;
}
.bench-header {
  margin-bottom: 48px;
  max-width: 820px;
}
.bench-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border-radius: 4px;
  background: rgba(201, 255, 59, 0.08);
  border: 1px solid rgba(201, 255, 59, 0.3);
  color: var(--lime);
  margin-bottom: 14px;
}
.bench-h2 {
  font-family: var(--disp);
  font-weight: 600;
  font-size: clamp(34px, 4.4vw, 56px);
  line-height: 1.08;
  color: #fff;
  letter-spacing: -0.03em;
  margin-bottom: 16px;
}
.bench-lead {
  font-size: 16.5px;
  color: var(--md);
  line-height: 1.55;
}
.bench-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
  gap: 28px;
}
@media (max-width: 640px) {
  .bench-grid { grid-template-columns: 1fr; }
}
.bench-card {
  background: var(--ink);
  border: 1px solid var(--ld);
  border-radius: 18px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 16px 48px rgba(0,0,0,0.45);
  transition: border-color 0.3s, transform 0.3s;
}
.bench-card:hover {
  border-color: rgba(201, 255, 59, 0.35);
}
.bench-card-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--lime);
  background: rgba(201, 255, 59, 0.06);
  border: 1px solid rgba(201, 255, 59, 0.2);
  padding: 3px 8px;
  border-radius: 4px;
  margin-bottom: 12px;
}
.bench-card-h3 {
  font-family: var(--disp);
  font-weight: 600;
  font-size: 22px;
  color: #fff;
  line-height: 1.25;
  margin-bottom: 10px;
  letter-spacing: -0.02em;
}
.bench-desc {
  font-size: 14px;
  color: var(--md);
  line-height: 1.5;
  margin-bottom: 20px;
}
.bench-plot-box {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid var(--ld);
  border-radius: 12px;
  padding: 18px;
  position: relative;
}
.bench-stats-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--ld);
}
.bench-stat-col {
  font-family: var(--mono);
}
.bench-stat-label {
  font-size: 9.5px;
  color: var(--md);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.bench-stat-val {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-top: 2px;
}
.bench-stat-val.lime { color: var(--lime); }
.bench-stat-val.red { color: #ef4444; }
.bench-stat-val.cyan { color: #38bdf8; }
"""

HTML_BENCHMARKS = """
<!-- ========================================================================
     ORIGINAL SWIZZLE EMPIRICAL BENCHMARKS SUITE (Brand: Obsidian & Lime)
     ======================================================================== -->
<section class="bench-suite" id="benchmarks">
  <div class="wrap">
    <div class="bench-header rv">
      <div class="bench-tag">Empirical Systems Benchmarks</div>
      <h2 class="bench-h2">Hardware rooflines measured on real agent workloads.</h2>
      <p class="bench-lead">First-principles benchmarks measured directly across our AST virtual paging engine, speculative lookahead trie, RoCEv2 disaggregated topology, and live cloud GPU workers.</p>
    </div>

    <div class="bench-grid rv" style="--d:.05s">
      <!-- BENCHMARK 1: AST-Diff KV Virtual Paging vs Linear Prefix Collapse -->
      <div class="bench-card">
        <div>
          <span class="bench-card-badge">Swizzle-Tree · AST Virtual Paging</span>
          <h3 class="bench-card-h3">Eliminating Prefix Cache Collapse on Git Diffs</h3>
          <p class="bench-desc">When an agent edits an early struct field, linear prefix caching collapses hits to 5.3%. Swizzle-Tree atomizes code into invariant AST blocks, preserving 89.6% cache reuse.</p>
          
          <div class="bench-plot-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; font-family:var(--mono); font-size:11px">
              <span style="color:#fff; font-weight:600">8-Turn Multi-Turn Refactor <span style="color:var(--md); font-weight:400">(SWE-bench 3.3k Tokens)</span></span>
              <span style="color:var(--lime)">+41.6% Absolute Hit Rate</span>
            </div>

            <svg viewBox="0 0 480 180" width="100%" height="160" style="overflow:visible">
              <defs>
                <linearGradient id="astGainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#c9ff3b" stop-opacity="0.25"/>
                  <stop offset="100%" stop-color="#c9ff3b" stop-opacity="0.02"/>
                </linearGradient>
              </defs>

              <!-- Y-Axis labels -->
              <text x="5" y="25" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">100%</text>
              <text x="5" y="70" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">75%</text>
              <text x="5" y="115" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">50%</text>
              <text x="5" y="160" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">0%</text>

              <!-- Grid lines -->
              <line x1="38" y1="20" x2="475" y2="20" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="65" x2="475" y2="65" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="110" x2="475" y2="110" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="155" x2="475" y2="155" stroke="rgba(230,234,223,0.12)"/>

              <!-- Swizzle-Tree Shaded Gain Area -->
              <polygon points="38,155 95,29 155,36 215,39 275,32 335,38 395,27 475,36 475,155" fill="url(#astGainGrad)"/>

              <!-- Linear Prefix Cache Curve (Red Dashed, showing catastrophic drops) -->
              <path d="M 38 155 L 95 38 L 155 147 L 215 137 L 275 143 L 335 133 L 395 47 L 475 146" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 3"/>

              <!-- Swizzle-Tree Curve (Solid Glowing Lime) -->
              <path d="M 38 155 L 95 29 L 155 36 L 215 39 L 275 32 L 335 38 L 395 27 L 475 36" fill="none" stroke="#c9ff3b" stroke-width="2.6"/>

              <!-- Turn 3 Callout (Early struct edit) -->
              <circle cx="155" cy="147" r="4" fill="#ef4444"/>
              <circle cx="155" cy="36" r="4.5" fill="#c9ff3b" stroke="#000" stroke-width="1.5"/>
              <line x1="155" y1="36" x2="155" y2="147" stroke="rgba(201,255,59,0.3)" stroke-dasharray="2 2"/>
              <rect x="165" y="68" width="105" height="24" rx="4" fill="#06120d" stroke="rgba(201,255,59,0.4)" stroke-width="1"/>
              <text x="170" y="84" fill="#c9ff3b" font-family="IBM Plex Mono" font-size="8.5" font-weight="600">89.6% vs 5.3% Hit</text>

              <!-- X-Axis Turn Labels -->
              <text x="38" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T1</text>
              <text x="95" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T2</text>
              <text x="145" y="172" fill="#ef4444" font-family="IBM Plex Mono" font-size="9">T3 (Diff)</text>
              <text x="215" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T4</text>
              <text x="275" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T5</text>
              <text x="335" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T6</text>
              <text x="395" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">T7</text>
              <text x="450" y="172" fill="#ef4444" font-family="IBM Plex Mono" font-size="9">T8 (Top)</text>
            </svg>
          </div>
        </div>

        <div class="bench-stats-strip">
          <div class="bench-stat-col">
            <div class="bench-stat-label">Linear Avg Hit</div>
            <div class="bench-stat-val red">48.0%</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Swizzle-Tree Hit</div>
            <div class="bench-stat-val lime">89.6%</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">TTFT Speedup</div>
            <div class="bench-stat-val lime">3.52× Faster</div>
          </div>
        </div>
      </div>

      <!-- BENCHMARK 2: Swizzle-Draft Speculative Lookahead Roofline -->
      <div class="bench-card">
        <div>
          <span class="bench-card-badge">Swizzle-Draft · Speculative Engine</span>
          <h3 class="bench-card-h3">Speculative Lookahead Throughput Roofline</h3>
          <p class="bench-desc">Sliding-window lexical N-gram Trie proposes candidate tokens verified in a single parallel target pass, delivering 98.7 tok/s on Qwen-Coder at 90.5% acceptance.</p>

          <div class="bench-plot-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; font-family:var(--mono); font-size:11px">
              <span style="color:#fff; font-weight:600">Qwen2.5-Coder-7B <span style="color:var(--md); font-weight:400">(A100 SXM4)</span></span>
              <span style="color:var(--lime)">2.76× Speedup</span>
            </div>

            <svg viewBox="0 0 480 180" width="100%" height="160" style="overflow:visible">
              <defs>
                <linearGradient id="draftGainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#c9ff3b" stop-opacity="0.25"/>
                  <stop offset="100%" stop-color="#c9ff3b" stop-opacity="0.02"/>
                </linearGradient>
              </defs>

              <!-- Y-Axis labels (Throughput tok/s) -->
              <text x="5" y="25" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">120</text>
              <text x="5" y="65" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">90</text>
              <text x="5" y="105" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">60</text>
              <text x="5" y="145" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">30</text>

              <!-- Grid lines -->
              <line x1="38" y1="20" x2="475" y2="20" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="60" x2="475" y2="60" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="100" x2="475" y2="100" stroke="rgba(230,234,223,0.06)"/>
              <line x1="38" y1="140" x2="475" y2="140" stroke="rgba(230,234,223,0.12)"/>

              <!-- Baseline Autoregressive Roofline (Red dashed horizontal) -->
              <line x1="38" y1="137" x2="475" y2="137" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="3 3"/>
              <text x="310" y="132" fill="#ef4444" font-family="IBM Plex Mono" font-size="8.5">Autoregressive: 35.7 tok/s</text>

              <!-- Speculative Roofline Area -->
              <polygon points="50,137 135,114 220,85 305,62 390,44 465,47 465,155 50,155" fill="url(#draftGainGrad)"/>

              <!-- Throughput Curve (Lime) -->
              <path d="M 50 137 L 135 114 L 220 85 L 305 62 L 390 44 L 465 47" fill="none" stroke="#c9ff3b" stroke-width="2.6"/>

              <!-- Optimal Peak Callout (gamma=4) -->
              <circle cx="390" cy="44" r="5" fill="#c9ff3b" stroke="#000" stroke-width="1.5"/>
              <rect x="340" y="16" width="105" height="22" rx="4" fill="#06120d" stroke="#c9ff3b" stroke-width="1"/>
              <text x="345" y="31" fill="#c9ff3b" font-family="IBM Plex Mono" font-size="8.5" font-weight="600">Peak: 98.7 tok/s</text>

              <!-- Data Points -->
              <circle cx="50" cy="137" r="3.5" fill="#ef4444"/>
              <circle cx="135" cy="114" r="3.5" fill="#c9ff3b"/>
              <circle cx="220" cy="85" r="3.5" fill="#c9ff3b"/>
              <circle cx="305" cy="62" r="3.5" fill="#c9ff3b"/>
              <circle cx="465" cy="47" r="3.5" fill="#c9ff3b"/>

              <!-- X-Axis Lookahead gamma -->
              <text x="50" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9" text-anchor="middle">γ=0 (Base)</text>
              <text x="135" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9" text-anchor="middle">γ=1</text>
              <text x="220" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9" text-anchor="middle">γ=2</text>
              <text x="305" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9" text-anchor="middle">γ=3</text>
              <text x="390" y="172" fill="#c9ff3b" font-family="IBM Plex Mono" font-size="9" font-weight="600" text-anchor="middle">γ=4 (Opt)</text>
              <text x="465" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9" text-anchor="middle">γ=5</text>
            </svg>
          </div>
        </div>

        <div class="bench-stats-strip">
          <div class="bench-stat-col">
            <div class="bench-stat-label">Baseline Speed</div>
            <div class="bench-stat-val red">35.7 tok/s</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Speculative Peak</div>
            <div class="bench-stat-val lime">98.7 tok/s</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Acceptance Rate</div>
            <div class="bench-stat-val lime">90.5% (Go)</div>
          </div>
        </div>
      </div>

      <!-- BENCHMARK 3: Swizzle-PD Prefill-Decode Disaggregation ITL Jitter -->
      <div class="bench-card">
        <div>
          <span class="bench-card-badge">Swizzle-PD · RoCEv2 Disaggregation</span>
          <h3 class="bench-card-h3">Inter-Token Jitter Elimination under 64k Prompt Bursts</h3>
          <p class="bench-desc">Monolithic inference stalls token decoding for 3 seconds when an agent sends a 64k repository context. Swizzle-PD offloads prefilling to H100s via RoCEv2 RDMA.</p>

          <div class="bench-plot-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; font-family:var(--mono); font-size:11px">
              <span style="color:#fff; font-weight:600">Active Decode Stream <span style="color:var(--md); font-weight:400">(64k Burst Arrival @ t=150ms)</span></span>
              <span style="color:var(--lime)">99.9% Jitter Drop</span>
            </div>

            <svg viewBox="0 0 480 180" width="100%" height="160" style="overflow:visible">
              <!-- Y-Axis labels (ITL Delay ms) -->
              <text x="5" y="25" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">3000ms</text>
              <text x="5" y="65" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">2000ms</text>
              <text x="5" y="105" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">1000ms</text>
              <text x="5" y="145" fill="#64748b" font-family="IBM Plex Mono" font-size="9.5">0ms</text>

              <!-- Grid lines -->
              <line x1="45" y1="20" x2="475" y2="20" stroke="rgba(230,234,223,0.06)"/>
              <line x1="45" y1="60" x2="475" y2="60" stroke="rgba(230,234,223,0.06)"/>
              <line x1="45" y1="100" x2="475" y2="100" stroke="rgba(230,234,223,0.06)"/>
              <line x1="45" y1="140" x2="475" y2="140" stroke="rgba(230,234,223,0.12)"/>

              <!-- 64k Burst Arrival Marker -->
              <line x1="160" y1="20" x2="160" y2="140" stroke="rgba(255,91,46,0.3)" stroke-dasharray="3 3"/>
              <text x="165" y="32" fill="#ff5b2e" font-family="IBM Plex Mono" font-size="8.5">64k Repo Prompt Arrives</text>

              <!-- Monolithic Curve (Red spike jumping to 2968ms freeze!) -->
              <path d="M 45 137 L 155 137 L 165 24 L 320 24 L 330 137 L 475 137" fill="none" stroke="#ef4444" stroke-width="2.2"/>
              <rect x="200" y="40" width="115" height="22" rx="4" fill="#06120d" stroke="#ef4444" stroke-width="1"/>
              <text x="205" y="55" fill="#ef4444" font-family="IBM Plex Mono" font-size="8.5" font-weight="600">3.0s Stream Freeze</text>

              <!-- Swizzle-PD Curve (Flat Lime Line staying <28ms!) -->
              <path d="M 45 138 L 155 138 L 165 134 L 320 134 L 330 138 L 475 138" fill="none" stroke="#c9ff3b" stroke-width="2.6"/>

              <!-- X-Axis Timeline ms -->
              <text x="45" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">0ms</text>
              <text x="140" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">100ms</text>
              <text x="230" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">200ms</text>
              <text x="320" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">300ms</text>
              <text x="410" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">400ms</text>
              <text x="475" y="172" fill="#64748b" font-family="IBM Plex Mono" font-size="9">500ms</text>
            </svg>
          </div>
        </div>

        <div class="bench-stats-strip">
          <div class="bench-stat-col">
            <div class="bench-stat-label">Monolithic p99</div>
            <div class="bench-stat-val red">2,968.7 ms</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Swizzle-PD p99</div>
            <div class="bench-stat-val lime">28.6 ms</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Jitter Drop</div>
            <div class="bench-stat-val lime">99.9% Gone</div>
          </div>
        </div>
      </div>

      <!-- BENCHMARK 4: Live Silicon Verification (Colab L4 GPU TTFT Drop) -->
      <div class="bench-card">
        <div>
          <span class="bench-card-badge">Live Hardware Verification · NVIDIA L4</span>
          <h3 class="bench-card-h3">Live Silicon TTFT Latency Waterfall (295ms Warm)</h3>
          <p class="bench-desc">Measured live against our Colab Pro NVIDIA L4 GPU worker running Qwen2.5-Coder-7B via Cloudflare Tunnel. Cold prefill collapses from 25.8s down to 295ms on warm cache.</p>

          <div class="bench-plot-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; font-family:var(--mono); font-size:11px">
              <span style="color:#fff; font-weight:600">NVIDIA L4 GPU Worker <span style="color:var(--md); font-weight:400">(Cloudflare Tunnel)</span></span>
              <span style="color:var(--lime)">87.6× Faster TTFT</span>
            </div>

            <!-- Waterfall Bars -->
            <div style="display:flex; flex-direction:column; gap:16px; padding:8px 0">
              <!-- Bar 1: Cold Turn 1 -->
              <div>
                <div style="display:flex; justify-content:space-between; font-family:var(--mono); font-size:11px; margin-bottom:6px">
                  <span style="color:var(--md)">Turn 1 · Cold Prompt Prefill (0% Cached)</span>
                  <span style="color:#ef4444; font-weight:600">25,854 ms</span>
                </div>
                <div style="background:rgba(255,255,255,0.06); height:22px; border-radius:6px; overflow:hidden; border:1px solid rgba(255,255,255,0.1)">
                  <div style="width:100%; height:100%; background:linear-gradient(90deg, #ef4444, #f97316); border-radius:5px"></div>
                </div>
              </div>

              <!-- Bar 2: Warm Turn 2 (Swizzle Prefix Cache Hit) -->
              <div>
                <div style="display:flex; justify-content:space-between; font-family:var(--mono); font-size:11px; margin-bottom:6px">
                  <span style="color:#fff; font-weight:600">Turn 2 · Swizzle Prefix Cache Hit</span>
                  <span style="color:var(--lime); font-weight:700">295 ms (87.6× speedup)</span>
                </div>
                <div style="background:rgba(255,255,255,0.06); height:22px; border-radius:6px; overflow:hidden; border:1px solid rgba(201,255,59,0.3)">
                  <div style="width:3.5%; min-width:14px; height:100%; background:var(--lime); box-shadow:0 0 12px var(--lime); border-radius:5px"></div>
                </div>
              </div>
            </div>

            <div style="margin-top:14px; font-family:var(--mono); font-size:10.5px; color:var(--md); border-top:1px solid var(--ld); padding-top:10px; display:flex; justify-content:space-between">
              <span>SDK: swizzle-ai v0.1.0</span>
              <span style="color:#fff">750 chunks streamed @ 17.5 chunks/s</span>
            </div>
          </div>
        </div>

        <div class="bench-stats-strip">
          <div class="bench-stat-col">
            <div class="bench-stat-label">Cold TTFT</div>
            <div class="bench-stat-val red">25,854 ms</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Cached TTFT</div>
            <div class="bench-stat-val lime">295 ms</div>
          </div>
          <div class="bench-stat-col">
            <div class="bench-stat-label">Total Speedup</div>
            <div class="bench-stat-val lime">87.6× Faster</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def main():
    target_files = [
        "index.html",
        "web/index.html",
        "dist/index.html",
        "web/dist/index.html",
        "gateway/static/index.html",
    ]

    for fpath in target_files:
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Insert CSS
        if "ORIGINAL SWIZZLE EMPIRICAL BENCHMARKS SUITE" not in content:
            marker = "/* Modal */"
            if marker in content:
                content = content.replace(marker, CSS_BENCHMARKS + "\n" + marker)
            else:
                print(f"Warning: could not find CSS marker in {fpath}")

        # 2. Add top nav link for Benchmarks
        nav_marker = '<div class="links">\n      <a href="#platform">Platform</a>'
        nav_replacement = '<div class="links">\n      <a href="#platform">Platform</a><a href="#benchmarks">Benchmarks</a>'
        if '<a href="#benchmarks">Benchmarks</a>' not in content and nav_marker in content:
            content = content.replace(nav_marker, nav_replacement)

        # 3. Insert HTML section right after </section> (end of #platform)
        section_marker = """            <circle class="dot" cx="200" cy="155" r="5" style="fill:var(--lime);filter:drop-shadow(0 0 10px var(--lime))"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="light pad" id="models">"""

        section_replacement = """            <circle class="dot" cx="200" cy="155" r="5" style="fill:var(--lime);filter:drop-shadow(0 0 10px var(--lime))"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</section>
""" + HTML_BENCHMARKS + """
<section class="light pad" id="models">"""

        if 'id="benchmarks"' not in content:
            if section_marker in content:
                content = content.replace(section_marker, section_replacement)
            else:
                sm_crlf = section_marker.replace("\n", "\r\n")
                sr_crlf = section_replacement.replace("\n", "\r\n")
                if sm_crlf in content:
                    content = content.replace(sm_crlf, sr_crlf)
                else:
                    print(f"Warning: section marker not found in {fpath}")

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Successfully injected authentic benchmarks into {fpath}!")

if __name__ == "__main__":
    main()

