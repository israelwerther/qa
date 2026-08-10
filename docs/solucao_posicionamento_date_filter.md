# Solução para Posicionamento Dinâmico do Componente Date Filter

## 1. Problema Identificado
O componente `date_filter` (filtro de período/calendário usado no hub de dashboards) possuía alinhamento fixo à esquerda (`tw-left-0`) no seu menu suspenso (*dropdown* de 288px de largura).

Quando o filtro era posicionado na extremidade direita de uma página ou barra de filtros:
- O painel abria da borda esquerda do botão para a direita.
- Como o espaço à direita era insuficiente, o calendário transbordava a tela (*overflow* horizontal), cortando o conteúdo fora da visão do usuário.

Da mesma forma, forçar um alinhamento estático à direita (`tw-right-0`) causaria o mesmo problema invertido caso o botão estivesse posicionado na extremidade esquerda da tela.

---

## 2. Solução Proposta
Implementação de **posicionamento dinâmico automático com detecção de colisões no Viewport** usando Alpine.js no próprio componente frontend.

### Regra de Negócio Visual:
1. Sempre que o usuário clicar para abrir o filtro (`open = true`), o Alpine mede a posição do botão na tela via `getBoundingClientRect()`.
2. Se `posição_esquerda + largura_dropdown (288px)` for maior que a `largura_disponível_do_viewport - 16px`:
   - O dropdown deve alinhar à **direita** (`tw-right-0`).
3. Caso contrário (há espaço suficiente para abrir à esquerda):
   - O dropdown deve alinhar à **esquerda** (`tw-left-0`).
4. Permite override manual opcional via propriedade `align` (`'left'`, `'right'` ou `'auto'`).

---

## 3. Alterações Necessárias nos Arquivos

### Arquivo 1: `fiscallizeon/dashboards/components/date_filter/date_filter.py`

Adicionar o parâmetro `align="auto"` no contexto padrão da classe do componente:

```python
from django_components import component


@component.register("date_filter")
class DateFilter(component.Component):
    template_name = "date_filter/date_filter.html"

    def get_context_data(self, trigger_class="tw-min-h-[4.5rem]", align="auto"):
        return {
            "trigger_class": trigger_class,
            "align": align,
        }
```

---

### Arquivo 2: `fiscallizeon/dashboards/components/date_filter/date_filter.html`

Adicionar a função `checkPosition()`, os observadores de estado e o binding dinâmico de classe `:class="alignRight ? 'tw-right-0' : 'tw-left-0'"`:

```html
<div
  x-data="{
    open: false,
    alignRight: false,
    forcedAlign: '{{ align|default:'auto' }}',
    tempStart: '',
    tempEnd: '',
    activeRange: null,

    get store() { return Alpine.store('dashboard') },

    checkPosition() {
      if (this.forcedAlign === 'right') {
        this.alignRight = true
        return
      }
      if (this.forcedAlign === 'left') {
        this.alignRight = false
        return
      }
      const rect = this.$el.getBoundingClientRect()
      const dropdownWidth = 288 // 72 * 4px (tw-w-72)
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth
      this.alignRight = (rect.left + dropdownWidth) > (viewportWidth - 16)
    },

    get displayText() {
      const s = this.store.startDate
      const e = this.store.endDate
      if (!s || !e) return 'Selecionar período'
      if (this.activeRange) return this.activeRange
      return this.formatDate(s) + ' - ' + this.formatDate(e)
    },

    formatDate(str) {
      if (!str) return ''
      const d = new Date(str + 'T12:00:00')
      return d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' })
    },

    toISO(d) {
      return d.toISOString().split('T')[0]
    },

    applyRange(label) {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      let s, e

      if (label === 'Hoje') {
        s = e = new Date(today)
      } else if (label === 'Ontem') {
        const y = new Date(today); y.setDate(y.getDate() - 1)
        s = e = y
      } else if (label === 'Últimos 7 dias') {
        s = new Date(today); s.setDate(s.getDate() - 6)
        e = new Date(today)
      } else if (label === 'Últimos 30 dias') {
        s = new Date(today); s.setDate(s.getDate() - 29)
        e = new Date(today)
      } else if (label === 'Este mês') {
        s = new Date(today.getFullYear(), today.getMonth(), 1)
        e = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      } else if (label === 'Último mês') {
        s = new Date(today.getFullYear(), today.getMonth() - 1, 1)
        e = new Date(today.getFullYear(), today.getMonth(), 0)
      }

      this.store.startDate = this.toISO(s)
      this.store.endDate   = this.toISO(e)
      this.activeRange = label
      this.open = false
      this._dispatchFilters()
    },

    applyCustom() {
      if (!this.tempStart || !this.tempEnd) return
      if (this.tempStart > this.tempEnd) {
        [this.tempStart, this.tempEnd] = [this.tempEnd, this.tempStart]
      }
      this.store.startDate = this.tempStart
      this.store.endDate   = this.tempEnd
      this.activeRange = null
      this.open = false
      this._dispatchFilters()
    },

    _dispatchFilters() {
      const url = new URL(window.location.href)
      const s = this.store.startDate
      const e = this.store.endDate
      if (s && e) {
        url.searchParams.set('period', s + ',' + e)
      } else {
        url.searchParams.delete('period')
      }
      history.replaceState({}, '', url.toString())

      window.dispatchEvent(new CustomEvent('dashboard:filters-changed', {
        detail: {
          startDate: this.store.startDate,
          endDate:   this.store.endDate,
          what:      this.store.activeWhat    || '',
          whatIds:   this.store.activeWhatIds || [],
        },
      }))
    },

    init() {
      this.tempStart = this.store.startDate || ''
      this.tempEnd   = this.store.endDate   || ''
      this.detectActiveRange()

      this.$watch('open', v => {
        if (v) this.checkPosition()
      })

      this.$watch('store.startDate', v => {
        this.tempStart = v || ''
        this.detectActiveRange()
      })
      this.$watch('store.endDate', v => {
        this.tempEnd = v || ''
        this.detectActiveRange()
      })
    },

    detectActiveRange() {
      const s = this.store.startDate
      const e = this.store.endDate
      if (!s || !e) return

      const today = new Date(); today.setHours(0,0,0,0)
      const iso = d => d.toISOString().split('T')[0]

      const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1)
      const last7s    = new Date(today); last7s.setDate(last7s.getDate() - 6)
      const last30s   = new Date(today); last30s.setDate(last30s.getDate() - 29)
      const thisMonthS = new Date(today.getFullYear(), today.getMonth(), 1)
      const thisMonthE = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      const lastMonthS = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      const lastMonthE = new Date(today.getFullYear(), today.getMonth(), 0)

      const map = [
        ['Hoje',           iso(today),      iso(today)],
        ['Ontem',          iso(yesterday),  iso(yesterday)],
        ['Últimos 7 dias', iso(last7s),     iso(today)],
        ['Últimos 30 dias',iso(last30s),    iso(today)],
        ['Este mês',       iso(thisMonthS), iso(thisMonthE)],
        ['Último mês',     iso(lastMonthS), iso(lastMonthE)],
      ]

      const match = map.find(([,ms,me]) => ms === s && me === e)
      this.activeRange = match ? match[0] : null
    },
  }"
  x-init="init()"
  @mousedown.outside="open = false"
  @resize.window.debounce.100ms="if (open) checkPosition()"
  class="tw-relative tw-min-w-0"
>
  <!-- Botão gatilho -->
  <button
    type="button"
    @click="open = !open"
    aria-haspopup="dialog"
    :aria-expanded="open"
    class="tw-flex tw-items-center tw-gap-2 tw-w-full tw-min-w-0 tw-min-h-[4.5rem] tw-rounded-md tw-border tw-border-gray-300 tw-bg-white tw-px-4 tw-py-3 tw-text-sm tw-font-medium tw-text-gray-700 hover:tw-bg-gray-50 tw-transition-colors {{trigger_class}}"
  >
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="tw-flex-shrink-0 tw-text-gray-400" aria-hidden="true">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
    <span class="tw-flex-1 tw-text-left tw-truncate" x-text="displayText"></span>
    <svg width="14" height="8" viewBox="0 0 14 8" fill="none" :class="{'tw-rotate-180': open}" class="tw-transition-transform tw-flex-shrink-0" aria-hidden="true">
      <path d="M1 1L7 7L13 1" stroke="#D0D5DD" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>

  <!-- Dropdown -->
  <div
    x-show="open"
    x-transition:enter="tw-transition tw-ease-out tw-duration-100"
    x-transition:enter-start="tw-opacity-0 tw-scale-95"
    x-transition:enter-end="tw-opacity-100 tw-scale-100"
    x-transition:leave="tw-transition tw-ease-in tw-duration-75"
    x-transition:leave-start="tw-opacity-100 tw-scale-100"
    x-transition:leave-end="tw-opacity-0 tw-scale-95"
    :class="alignRight ? 'tw-right-0' : 'tw-left-0'"
    class="tw-absolute tw-z-30 tw-mt-1 tw-w-72 tw-max-w-[calc(100vw-2rem)] tw-rounded-md tw-bg-white tw-shadow-lg tw-ring-1 tw-ring-black tw-ring-opacity-5"
    style="display: none;"
  >
```

---

## 4. Benefícios
- **100% Automático**: Funciona sem necessidade de alterar templates que consomem `{% component 'date_filter' %}`.
- **Responsivo**: Recalcula dinamicamente se o usuário redimensionar a janela enquanto o dropdown estiver aberto.
- **Proteção Extra em Telas Pequenas**: `tw-max-w-[calc(100vw-2rem)]` evita estouro horizontal em visores mobile abaixo de 300px.
