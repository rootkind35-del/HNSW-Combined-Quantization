import os

path = r'f:\ANN\dashboard\public\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

insert = """  <!-- Distributed CF -->
  <tr class="bg-indigo-50/50 hover:bg-indigo-50 transition border-l-4 border-indigo-600">
  <td class="py-2.5 px-4 font-bold text-indigo-900 flex items-center gap-2">
    Distributed Collaborative Filtering
  </td>
  <td class="py-2.5 px-4 text-center font-mono font-bold text-indigo-800" id="eval-cfdistributed-qps">--</td>
  <td class="py-2.5 px-4 text-center font-mono text-slate-800" id="eval-cfdistributed-mean">--</td>
  <td class="py-2.5 px-4 text-center font-mono text-slate-700" id="eval-cfdistributed-p95">--</td>
  <td class="py-2.5 px-4 text-center font-mono font-bold text-emerald-800" id="eval-cfdistributed-recall">--</td>
  <td class="py-2.5 px-4 text-center text-indigo-800 font-bold text-[12px]">Phân tán Dot-Product</td>
  </tr>"""

text = text.replace('  </tr>\n  </tbody>', '  </tr>\n' + insert + '\n  </tbody>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

path2 = r'f:\ANN\dashboard\public\js\app.js'
with open(path2, 'r', encoding='utf-8') as f:
    text2 = f.read()

text2 = text2.replace("two_tier: 'eval-twotier'", "two_tier: 'eval-twotier',\n    cf_distributed: 'eval-cfdistributed'")
text2 = text2.replace('two_tier: "75.0%"', 'two_tier: "75.0%",\n    cf_distributed: "Phân tán (Shards)"')

with open(path2, 'w', encoding='utf-8') as f:
    f.write(text2)
