<template>
  <div class="min-h-screen bg-black text-white flex flex-col workspace-root">
    <!-- Header -->
    <header class="h-9 flex items-center justify-between px-2.5 border-b border-white/10 bg-black">
      <div class="flex items-center gap-2">
        <div class="h-6 w-6 shrink-0">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sidian logo">
            <path d="M12 2 22 22H2z" fill="#6b21a8" />
          </svg>
        </div>
        <span class="text-[12px] font-semibold">Sidian AI</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-[10px] text-white/50">Free plan</span>
        <span class="text-white/30">·</span>
        <button class="text-[10px] text-white/70 hover:text-white transition" @click="handleUpgrade">Upgrade</button>
        <div class="h-6 w-6 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-600 border border-white/15 shadow-inner flex items-center justify-center text-[9px] font-semibold text-white">
          U
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden min-w-0 min-h-0 workspace-shell relative">
      <!-- Icon rail -->
      <aside class="w-12 bg-white/5 backdrop-blur-lg border-r border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)] flex flex-col items-center py-2 space-y-1.5 overflow-visible relative z-30">
        <template v-for="icon in railIcons" :key="icon.id">
          <div
            v-if="icon.id === 'timesheet'"
            class="relative group"
            @mouseenter="openTimesheetMenu"
            @mouseleave="closeTimesheetMenu"
      >
            <button
              class="relative h-8 w-8 rounded border border-transparent flex items-center justify-center text-white/60 hover:text-white hover:border-white/10 transition"
              :aria-label="icon.label"
              :class="activeRail === icon.id ? 'text-white border-white/20 bg-white/5' : ''"
              @click="handleTimesheetNav(timesheetSection)"
            >
              <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-purple-500 rounded-r" v-if="icon.id === activeRail"></span>
              <component :is="icon.component" class="w-5 h-5" />
            </button>
            <div
              v-if="timesheetMenuOpen"
              class="absolute left-full top-0 ml-3 z-20 min-w-[200px]"
            >
              <div class="bg-[#0f0f0f] border border-white/12 rounded-2xl shadow-[0_16px_36px_rgba(0,0,0,0.5)] p-3 space-y-2">
                <div class="pb-2 border-b border-white/10 flex items-center justify-between">
                  <p class="text-[13px] font-semibold text-white/90">Timeline</p>
                </div>
                <div class="space-y-1.5">
                  <TimelineMenuItem
                    v-for="item in timesheetMenuItems"
                    :key="item.id"
                    :icon="item.component"
                    :label="item.label"
                    :active="timesheetSection === item.id"
                    @click="handleTimesheetNav(item.id)"
                  />
                </div>
              </div>
            </div>
          </div>
          <div
            v-else
            class="relative group"
            @mouseenter="showSimpleMenu(icon.id)"
            @mouseleave="hideSimpleMenu"
          >
            <button
              class="relative h-8 w-8 rounded border border-transparent flex items-center justify-center text-white/60 hover:text-white hover:border-white/10 transition"
              :aria-label="icon.label"
                :class="activeRail === icon.id ? 'text-white border-white/20 bg-white/5' : ''"
                @click="setActivePage(icon.id)"
              >
                <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-purple-500 rounded-r" v-if="icon.id === activeRail"></span>
                <component :is="icon.component" class="w-5 h-5" />
              </button>
            <div
              v-if="hoveredSimpleMenu === icon.id"
              class="absolute left-full top-0 ml-3 z-20 bg-[#0f0f0f] border border-white/15 rounded-xl shadow-2xl min-w-[180px] py-2"
              @mouseenter="showSimpleMenu(icon.id)"
              @mouseleave="hideSimpleMenu"
            >
              <div class="px-3 py-1.5 text-sm font-semibold text-white/80">{{ icon.label }}</div>
            </div>
          </div>
        </template>
      </aside>

      <!-- Floating action rail (outside the sidebar, chat only) -->
      <div v-if="activePage === 'home'" class="absolute select-none pointer-events-none" :style="sidebarRailStyle">
        <div
          class="group relative flex flex-col items-center gap-2 px-2 py-3 rounded-full bg-[#0b0b0b]/95 border shadow-[0_24px_58px_rgba(0,0,0,0.55)] backdrop-blur-[6px] pointer-events-auto transition-shadow duration-500"
          :class="isSidebarCollapsed ? 'border-[#1a1a1a] shadow-[0_18px_42px_rgba(0,0,0,0.6)]' : 'border-white/14'"
        >
          <div class="absolute inset-[-12px] rounded-full border border-[rgba(147,51,234,0.55)] shadow-[0_0_24px_6px_rgba(147,51,234,0.4)] pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-1000 ease-out"></div>
          <div class="absolute inset-[-32px] rounded-full bg-[radial-gradient(circle_at_center,_rgba(147,51,234,0.7)_0%,_rgba(147,51,234,0.35)_35%,_rgba(147,51,234,0.1)_60%,_transparent_88%)] blur-[42px] pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-1000 ease-out"></div>
          <template v-for="(action, index) in sidebarActions" :key="action.id">
            <button
              class="h-8 w-8 rounded-full border transition flex items-center justify-center shadow-[0_6px_14px_rgba(0,0,0,0.35)] pointer-events-auto"
              :class="[
                !isSidebarCollapsed && sidebarMode === action.id
                  ? 'bg-white/18 border-white/55 ring-1 ring-white/65 shadow-[0_10px_28px_rgba(255,255,255,0.12)] text-white'
                  : isSidebarCollapsed
                    ? 'bg-[#0b0b0b]/85 border-[#111] text-white/50'
                    : 'bg-white/4 border-white/10 text-white/75 hover:text-white hover:bg-white/10 hover:border-white/20',
                isRailActionFilled(action.id) ? 'text-purple-200' : ''
              ]"
              :title="action.label"
              :aria-label="action.label"
              @click="handleSidebarAction(action.id)"
            >
              <component
                :is="action.component"
                class="w-4 h-4 opacity-85"
                :class="[
                  !isSidebarCollapsed && sidebarMode === action.id ? 'opacity-100' : isSidebarCollapsed ? 'opacity-75' : 'opacity-90',
                  isRailActionFilled(action.id) ? 'text-purple-400' : !isSidebarCollapsed && sidebarMode === action.id ? 'text-white' : isSidebarCollapsed ? 'text-white/55' : 'text-current'
                ]"
              />
            </button>
            <div
              v-if="index !== sidebarActions.length - 1"
              class="h-5 w-px"
              :class="isSidebarCollapsed ? 'bg-[#111]' : 'bg-white/14'"
            ></div>
          </template>
        </div>
      </div>

      <!-- Conversation list -->
      <aside
        v-if="activePage === 'home' && !isSidebarCollapsed"
        class="bg-white/8 backdrop-blur-2xl border-r border-white/10 shadow-[0_22px_70px_rgba(0,0,0,0.45)] flex flex-col relative min-w-[200px] conversation-sidebar min-h-0 overflow-y-auto custom-scroll transition-all duration-300 ease-out"
        :style="sidebarStyle"
        >
        <!-- Resize handle -->
        <div
          class="absolute top-0 right-0 h-full w-2 cursor-col-resize z-50 pointer-events-auto"
          @mousedown.prevent="startSidebarResize"
        >
          <div class="absolute left-0 top-1/2 -translate-y-1/2 h-14 w-[6px] rounded-full bg-white/10 border border-white/15 shadow-[0_4px_12px_rgba(0,0,0,0.35)]"></div>
        </div>

        <template v-if="sidebarMode === 'history'">
          <div class="px-2.5 py-2 border-b border-white/10">
            <button
              class="w-full h-8 px-3 rounded bg-white/8 border border-white/12 text-[11px] font-semibold hover:bg-white/12 transition flex items-center gap-2"
              @click="startNewConversation"
              aria-label="Start a new agent conversation"
            >
              <span class="text-sm leading-none">+</span>
              <span class="tracking-wide">NEW AGENT</span>
            </button>
          </div>

          <div class="px-2.5 py-2.5 border-b border-white/10">
            <div class="relative">
              <input
                v-model="search"
                type="text"
                class="w-full rounded bg-white/5 border border-white/10 text-[12px] px-3 py-1.5 pl-8 placeholder-white/40 focus:outline-none focus:border-white/30"
                placeholder="Search agents..."
                aria-label="Search agents"
              />
              <svg class="absolute left-3 top-2.5 w-4 h-4 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div class="flex-1 min-h-0 overflow-y-auto custom-scroll pr-1">
            <div
              v-for="section in filteredConversationSections"
              :key="section.title"
              class="px-2.5 py-2"
            >
              <p class="text-[10px] uppercase tracking-[0.18em] text-white/35 mb-2 font-medium">{{ section.title }}</p>
              <div class="space-y-1">
                <button
                  v-for="conv in section.items"
                  :key="conv.id"
                  class="w-full text-left px-2.5 py-1.5 rounded bg-transparent border border-transparent hover:bg-white/5 transition group"
                  :class="activeConversationId === conv.id && activePage === 'home' ? 'bg-white/5 border-white/10' : ''"
                  @click="selectConversation(conv.id)"
                  @contextmenu.prevent.stop="openContextMenu($event, conv.id)"
                  @dblclick.stop.prevent="startRename(conv.id)"
                >
                  <div v-if="renamingConversationId === conv.id" class="space-y-1">
                    <div class="relative">
                      <input
                        type="text"
                        v-model="renameDraft"
                        class="w-full bg-[#1a1a1a] border border-white/20 rounded px-2 py-1 pr-4 text-[12px] font-semibold text-white focus:outline-none focus:border-white/40"
                        :ref="el => setRenameInputRef(conv.id, el as HTMLInputElement | null)"
                        @click.stop
                        @keydown.enter.stop.prevent="confirmRename(conv.id)"
                        @keydown.esc.stop.prevent="cancelRename"
                        @blur="confirmRename(conv.id)"
                      />
                      <span class="absolute right-2 top-1/2 -translate-y-1/2 w-px h-4 bg-white animate-pulse pointer-events-none"></span>
                    </div>
                    <p class="text-[10px] text-white/55">{{ conv.time }}</p>
                  </div>
                  <div v-else class="space-y-0.5">
                    <p class="text-[12px] font-semibold truncate" :title="conv.title">{{ conv.title }}</p>
                    <p class="text-[10px] text-white/55">{{ conv.time }}</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="sidebarMode === 'logs'">
          <div class="px-3 pt-4 pb-3">
            <div class="flex items-center justify-center text-center rounded-2xl border border-white/12 bg-white/5 px-4 py-3 shadow-[0_12px_26px_rgba(0,0,0,0.38)]">
              <div class="space-y-0.5">
                <p class="text-sm font-semibold text-white/90">Agent Thinking</p>
                <p class="text-[11px] text-white/55 leading-tight">Real-time reasoning and decisions</p>
              </div>
            </div>
          </div>
          <div class="flex-1 min-h-0 overflow-y-auto custom-scroll px-3 pb-4 space-y-3">
            <div v-if="!agentLogs.length" class="flex flex-col items-center justify-center text-center py-10 px-6 gap-3 border border-dashed border-white/15 rounded-2xl bg-white/5 shadow-[0_12px_30px_rgba(0,0,0,0.32)]">
              <div class="h-12 w-12 rounded-2xl bg-white/10 flex items-center justify-center border border-white/10 shadow-inner">
                <svg class="w-6 h-6 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div class="space-y-1 max-w-[260px]">
                <p class="text-white font-semibold text-sm">No logs yet</p>
                <p class="text-white/60 text-xs leading-relaxed">Agent thinking will appear here as you interact with the system.</p>
              </div>
            </div>

            <div
              v-for="log in agentLogs"
              :key="log.id"
              class="rounded-2xl p-4 transition-all duration-200 border-l-4 bg-white/5 border border-white/10 shadow-[0_10px_26px_rgba(0,0,0,0.35)]"
              :class="log.type === 'result' ? 'border-green-400/70' : log.type === 'error' ? 'border-red-400/70' : 'border-purple-400/70'"
            >
              <div class="flex items-center gap-3 mb-2">
                <span class="text-xs text-white/60 font-mono">{{ formatTimestamp(log.timestamp) }}</span>
                <span class="text-[10px] px-2 py-1 rounded-full bg-white/10 border border-white/10 text-white/65 uppercase tracking-wide">
                  {{ log.type || 'thinking' }}
                </span>
              </div>
              <div
                class="text-white/90 prose prose-invert prose-sm max-w-none prose-headings:text-white prose-p:text-white/90 prose-strong:text-white prose-code:text-purple-200 prose-code:bg-purple-900/40 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-pre:bg-white/5 prose-pre:border prose-pre:border-white/10 prose-ul:text-white/80 prose-ol:text-white/80 prose-li:text-white/80"
                style="background-color: transparent;"
                v-html="formatThinking(log.thinking)"
              ></div>
            </div>
          </div>
        </template>

        <template v-else-if="sidebarMode === 'docs'">
          <div class="flex flex-col h-full">
            <div class="px-3 pt-4 pb-3">
            <div class="flex items-center justify-center text-center rounded-2xl border border-white/12 bg-white/5 px-4 py-3 shadow-[0_12px_26px_rgba(0,0,0,0.38)]">
              <div class="space-y-0.5">
                <p class="text-sm font-semibold text-white/90">Models & Docs</p>
                <p class="text-[11px] text-white/55 leading-tight">Fetched from Speckle/search</p>
              </div>
            </div>
          </div>
            <div class="flex-1 min-h-0 overflow-y-auto custom-scroll px-4 pb-4 space-y-3">
              <div v-if="speckleViewerFetchLoading" class="space-y-3">
                <div v-for="i in 4" :key="i" class="animate-pulse rounded-2xl border border-white/10 bg-white/5 px-4 py-5 space-y-3 shadow-[0_10px_26px_rgba(0,0,0,0.35)]">
                  <div class="h-4 w-32 bg-white/15 rounded"></div>
                  <div class="h-3 w-3/4 bg-white/10 rounded"></div>
                  <div class="flex gap-2">
                    <div class="h-6 w-16 bg-white/10 rounded-full"></div>
                    <div class="h-6 w-20 bg-white/10 rounded-full"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="docListDocs.length === 0" class="flex flex-col items-center justify-center text-center py-12 px-6 gap-4 border border-dashed border-white/15 rounded-2xl bg-white/5 shadow-[0_12px_30px_rgba(0,0,0,0.32)]">
                <div class="h-12 w-12 rounded-2xl bg-white/10 flex items-center justify-center border border-white/10 shadow-inner">
                  <svg class="w-6 h-6 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div class="space-y-1 max-w-[260px]">
                  <p class="text-white font-semibold text-sm">No models or documents yet</p>
                  <p class="text-white/60 text-xs leading-relaxed">Ask Sid to fetch 3D models or related docs to see them here.</p>
                </div>
              </div>

              <div v-else class="space-y-3 pb-1">
                <p class="text-[11px] uppercase tracking-[0.16em] text-white/50 px-1">Available</p>
                <div
                  v-for="(doc, index) in docListDocs"
                  :key="doc.id || index"
                  @click="handleDocumentSelect(doc)"
                  class="p-3 md:p-4 rounded-2xl border border-white/12 bg-white/5 hover:bg-white/10 hover:border-purple-400/60 transition-all shadow-[0_12px_34px_rgba(0,0,0,0.38)] cursor-pointer doc-card"
                  :class="{ 'doc-card--compact': isDocsCompact }"
                >
                  <div class="flex items-start gap-3 sm:gap-4 w-full">
                    <div class="flex-shrink-0 w-11 h-11 bg-gradient-to-br from-purple-600 to-fuchsia-600 rounded-xl flex items-center justify-center shadow-lg border border-white/15">
                      <svg v-if="doc.metadata?.projectId && doc.metadata?.modelId" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                      <svg v-else class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0 space-y-1">
                      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 min-w-0">
                        <h4
                          class="font-semibold text-white break-words leading-tight"
                          :class="isDocsCompact ? 'text-sm line-clamp-2' : 'text-base line-clamp-2'"
                        >
                          {{ doc.title || doc.name || 'Untitled' }}
                        </h4>
                        <span
                          v-if="doc.metadata?.projectName && !isDocsCompact"
                          class="text-[11px] px-2 py-1 rounded-full bg-white/10 border border-white/10 text-white/70 truncate w-full sm:w-auto"
                        >
                          {{ doc.metadata.projectName }}
                        </span>
                      </div>
                      <p
                        v-if="doc.description && !isDocsCompact"
                        class="text-sm text-white/70 line-clamp-2 break-words"
                      >
                        {{ doc.description }}
                      </p>
                      <div v-if="isDocsCompact && doc.metadata?.projectKey" class="flex flex-wrap gap-2 pt-1 w-full">
                        <span class="text-[11px] px-2 py-1 bg-purple-900/40 border border-purple-500/50 text-purple-100 rounded-full">
                          {{ doc.metadata.projectKey }}
                        </span>
                      </div>
                      <div v-else class="flex flex-wrap gap-2 pt-1 w-full">
                        <span
                          v-if="doc.metadata?.projectKey"
                          class="text-[11px] px-2 py-1 bg-purple-900/40 border border-purple-500/50 text-purple-100 rounded-full"
                        >
                          {{ doc.metadata.projectKey }}
                        </span>
                        <span
                          v-if="doc.metadata?.modelId"
                          class="text-[11px] px-2 py-1 bg-white/10 border border-white/15 text-white/70 rounded-full"
                        >
                          Model: {{ doc.metadata.modelId }}
                        </span>
                        <span
                          v-if="doc.reason"
                          class="text-[11px] px-2 py-1 bg-white/10 border border-white/15 text-white/70 rounded-full"
                        >
                          {{ doc.reason }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div
          v-if="contextMenu.visible && contextMenu.convId"
          ref="contextMenuRef"
          class="absolute z-20 bg-[#111] border border-white/15 rounded-lg shadow-2xl min-w-[160px] overflow-hidden"
          :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
        >
          <button
            class="w-full text-left px-4 py-2 text-sm text-white/85 hover:bg-white/5 border-b border-white/10"
            @click="renameConversation(contextMenu.convId)"
          >
            Rename
          </button>
          <button
            class="w-full text-left px-4 py-2 text-sm text-red-300 hover:bg-red-600/20"
            @click="openDeleteDialog(contextMenu.convId)"
          >
            Delete
          </button>
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 bg-black flex overflow-hidden min-w-0 workspace-main">
        <div class="flex flex-col flex-1 min-h-0 w-full max-w-4xl max-w-full mx-auto py-4 px-3 gap-4 min-w-0">
          <div class="flex items-center justify-between flex-wrap gap-3"></div>

          <div v-if="activePage === 'home'" class="flex-1 min-h-0 flex">
            <div
              ref="viewerSplitContainer"
              class="flex flex-1 min-h-0"
              :class="showSpeckleViewer ? '' : 'justify-center'"
            >
              <div
                class="h-full w-full chat-frame overflow-hidden flex flex-col"
                :class="{ 'chat-frame--docked': showSpeckleViewer }"
                :style="showSpeckleViewer ? chatPaneStyle : undefined"
              >
                <template v-if="!activeChatLog.length">
                  <div class="flex-1 min-h-[360px] flex flex-col items-center justify-center gap-7 text-center px-5 -translate-y-8 md:-translate-y-10">
                    <div class="flex flex-col items-center gap-3">
                      <div class="h-24 w-24 shrink-0 -translate-y-1">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sidian logo">
                          <polygon
                            points="12 1 3.6 23 20.4 23"
                            fill="#6b21a8"
                          />
                        </svg>
                      </div>
                      <div class="flex items-center gap-2 text-[11px] text-white/65">
                        <span class="px-3 py-1 rounded-full bg-white/5 border border-white/12 shadow-[0_4px_16px_rgba(0,0,0,0.35)]">Free plan</span>
                        <button class="text-white/75 hover:text-white transition" @click="handleUpgrade">Upgrade</button>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="text-lg">✺</span>
                        <p class="text-[26px] font-semibold tracking-tight text-white/90" style="font-family: 'Georgia', 'Times New Roman', serif;">
                          {{ greetingMessage }}
                        </p>
                      </div>
                    </div>
                    <div class="w-full max-w-3xl">
                      <div class="relative">
                        <transition name="attachment-tray">
                          <div
                            v-if="attachments.length"
                            class="absolute bottom-full left-0 mb-2 w-full bg-[#1f1f1f] border border-white/12 rounded-xl shadow-[0_12px_28px_rgba(0,0,0,0.4)] px-3 py-2.5"
                          >
                            <div class="flex flex-wrap gap-2.5">
                              <AttachmentChip
                                v-for="(file, idx) in attachments"
                                :key="file.name + idx"
                                :file="file"
                                @remove="removeAttachment(idx)"
                              />
                            </div>
                          </div>
                        </transition>
                        <div class="relative rounded-full bg-[#1c1c1c] border border-white/12 shadow-[0_8px_22px_rgba(0,0,0,0.35)] px-4 h-16 flex items-center gap-4 text-left">
                          <button
                            class="h-9 w-9 rounded-full border border-white/12 bg-white/5 hover:bg-white/10 transition flex items-center justify-center flex-shrink-0"
                            aria-label="Attach"
                            @click="openFilePicker"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m-7-7h14" />
                            </svg>
                          </button>
                          <textarea
                            v-model="prompt"
                            ref="promptInput"
                            class="flex-1 bg-transparent border-0 focus:outline-none focus:ring-0 text-[14px] leading-[20px] text-white placeholder-white/55 resize-none min-h-[20px] max-h-[48px] overflow-y-auto py-0 px-2"
                            placeholder="How can I help you today?"
                            aria-label="Prompt input"
                            rows="1"
                            @keydown.enter.exact.prevent="handleSend"
                            @input="resizePrompt"
                          ></textarea>
                          <button
                            class="h-10 w-10 rounded-full flex items-center justify-center text-white flex-shrink-0 transition"
                            :class="(prompt.trim() || attachments.length) && !isSending ? 'bg-[#6b21a8] hover:bg-[#7c2cc7]' : 'bg-[#6b21a8]/50 cursor-not-allowed'"
                            aria-label="Send"
                            @click="handleSend"
                            :disabled="isSending || (!prompt.trim() && !attachments.length)"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>

                <template v-else>
                  <div class="flex-1 min-h-0 flex flex-col">
                    <div ref="chatContainer" class="flex-1 min-h-0 overflow-y-auto px-4 py-4 custom-scroll relative">
                      <div class="max-w-2xl mx-auto space-y-3">
                        <div
                          v-for="(entry, idx) in activeChatLog"
                          :key="idx"
                          class="flex gap-4 group"
                          :class="entry.role === 'user' ? 'justify-end' : 'justify-start'"
                        >
                          <div
                            class="flex flex-col max-w-[520px]"
                            :class="entry.role === 'user' ? 'items-end' : 'items-start'"
                          >
                            <div
                              v-if="entry.attachments?.length"
                              class="flex flex-wrap gap-2.5 mb-2 w-full"
                              :class="entry.role === 'user' ? 'justify-end' : 'justify-start'"
                            >
                              <AttachmentChip
                                v-for="file in entry.attachments"
                                :key="file"
                                :file="{ name: file, base64: '' }"
                                @remove="() => {}"
                              />
                            </div>
                            <div
                              class="w-auto inline-flex rounded-2xl px-3.5 py-3 leading-relaxed shadow-lg max-w-full"
                              :class="entry.role === 'user'
                                ? 'bg-[#2a2a2a] border border-white/10'
                                : 'bg-transparent'
                              "
                            >
                              <div v-if="entry.role === 'assistant'" class="prose prose-invert prose-sm max-w-none" v-html="entry.content"></div>
                              <div v-else class="whitespace-pre-wrap text-[12px] text-white/90">{{ entry.content }}</div>
                            </div>
                            <div
                              class="flex items-center gap-3 text-[11px] text-white/50 mt-1 opacity-0 group-hover:opacity-100 transition pointer-events-none group-hover:pointer-events-auto"
                              :class="entry.role === 'user' ? 'self-end' : 'self-start pl-1'"
                            >
                              <span>{{ formatEntryTime(entry) }}</span>
                              <template v-if="entry.role === 'user'">
                                <button class="hover:text-white transition" @click="resendEntry(entry)" title="Resend">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                    <path d="M4 4v6h6" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M20 20v-6h-6" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M20 9a8 8 0 00-14.14-5.14L4 10" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M4 15a8 8 0 0014.14 5.14L20 14" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                                <button class="hover:text-white transition" @click="editEntry(entry)" title="Edit">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                    <path d="M12 20h9" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                                <button class="hover:text-white transition" @click="copyEntry(entry)" title="Copy">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                              </template>
                              <template v-else>
                                <button class="hover:text-white transition" @click="copyEntry(entry)" title="Copy">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <rect x="9" y="9" width="11" height="11" rx="2" ry="2" />
                                    <rect x="4" y="4" width="11" height="11" rx="2" ry="2" />
                                  </svg>
                                </button>
                                <button class="hover:text-white transition" :class="entry.liked ? 'text-white' : ''" @click="toggleLike(entry)" title="Like">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                    <path d="M14 9V5a3 3 0 00-3-3l-3 6H5a2 2 0 00-2 2v7a2 2 0 002 2h7.5a2 2 0 001.94-1.52l1.1-4.4A2 2 0 0013.6 11H10" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M7 12v8" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                                <button class="hover:text-white transition" :class="entry.disliked ? 'text-white' : ''" @click="toggleDislike(entry)" title="Dislike">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                    <path d="M14 15v4a3 3 0 01-3 3l-3-6H5a2 2 0 01-2-2V7a2 2 0 012-2h7.5a2 2 0 011.94 1.52l1.1 4.4A2 2 0 0113.6 13H10" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M7 12V4" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                                <button class="hover:text-white transition" @click="retryAssistant(idx)" title="Retry">
                                  <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M4 4v5h5" stroke-linecap="round" stroke-linejoin="round" />
                                    <path d="M4 9a7 7 0 107-7" stroke-linecap="round" stroke-linejoin="round" />
                                  </svg>
                                </button>
                              </template>
                            </div>
                          </div>
                        </div>
                      </div>
                      <button
                        v-if="showScrollToBottom"
                        @click="scrollToBottom(true)"
                        class="absolute right-4 bottom-4 h-9 w-9 rounded-full bg-white/10 border border-white/20 backdrop-blur hover:bg-white/20 transition text-white flex items-center justify-center shadow-lg"
                        aria-label="Scroll to latest message"
                      >
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>

                    <div class="px-4 py-3">
                      <div class="max-w-3xl mx-auto space-y-2.5">
                        <div class="relative">
                          <transition name="attachment-tray">
                            <div
                              v-if="attachments.length"
                              class="absolute bottom-full left-0 mb-2 w-full bg-[#1f1f1f] border border-white/12 rounded-xl shadow-[0_12px_28px_rgba(0,0,0,0.4)] px-3 py-2.5"
                            >
                              <div class="flex flex-wrap gap-2.5">
                                <AttachmentChip
                                  v-for="(file, idx) in attachments"
                                  :key="file.name + idx"
                                  :file="file"
                                  @remove="removeAttachment(idx)"
                                />
                              </div>
                            </div>
                          </transition>

                          <div class="relative rounded-full bg-[#1c1c1c] border border-white/10 shadow-[0_8px_18px_rgba(0,0,0,0.28)] px-4 h-16 flex items-center gap-4">
                          <button
                            class="h-9 w-9 rounded-full border border-white/12 bg-white/5 hover:bg-white/10 transition flex items-center justify-center flex-shrink-0"
                            aria-label="Attach"
                            @click="openFilePicker"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m-7-7h14" />
                            </svg>
                          </button>
                          <textarea
                            v-model="prompt"
                            ref="promptInput"
                            class="flex-1 bg-transparent border-0 focus:outline-none focus:ring-0 text-[13px] leading-[20px] text-white placeholder-white/55 resize-none min-h-[20px] max-h-[48px] overflow-y-auto py-0 px-2"
                            placeholder="Reply..."
                            aria-label="Prompt input"
                            rows="1"
                            @keydown.enter.exact.prevent="handleSend"
                            @input="resizePrompt"
                          ></textarea>
                          <button
                            class="h-9 w-9 rounded-full flex items-center justify-center text-white flex-shrink-0 transition"
                            :class="(prompt.trim() || attachments.length) && !isSending ? 'bg-[#6b21a8] hover:bg-[#7c2cc7]' : 'bg-[#6b21a8]/50 cursor-not-allowed'"
                            aria-label="Send"
                            @click="handleSend"
                            :disabled="isSending || (!prompt.trim() && !attachments.length)"
                          >
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>
                        </div>

                        <div v-if="tags.length" class="flex flex-wrap items-center gap-2 text-[10px] text-white/50 pl-1">
                          <span
                            v-for="tag in tags"
                            :key="tag"
                            class="px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/75 tracking-[0.14em] uppercase"
                          >
                            {{ tag }}
                          </span>
                          <span class="ml-auto text-white/45">Shift + Enter for newline</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>

              <template v-if="showSpeckleViewer">
                <div class="viewer-resize-handle" @mousedown.prevent="startViewerResize">
                  <div class="viewer-resize-grip"></div>
                </div>

                <div
                  class="flex flex-col min-h-0 viewer-pane bg-[#2a2a2a] border-l border-[#3a3a3a] shadow-[0_22px_70px_rgba(0,0,0,0.45)]"
                  :style="viewerPaneStyle"
                >
                  <div class="relative flex-1 min-h-0 bg-[#2a2a2a] viewer-canvas-shell">
                    <button
                      class="viewer-close"
                      type="button"
                      @click="closeSpeckleViewer"
                      aria-label="Close viewer"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>

                    <div
                      v-if="speckleViewerFetchLoading && !selectedSpeckleModel"
                      class="absolute inset-0 flex items-center justify-center bg-[#2a2a2a]/90 backdrop-blur-sm z-10"
                    >
                      <div class="text-center space-y-2">
                        <div class="w-14 h-14 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                        <p class="text-slate-200 text-sm">Loading models…</p>
                      </div>
                    </div>
                    <div
                      v-else-if="speckleViewerFetchError && !selectedSpeckleModel"
                      class="absolute inset-0 flex items-center justify-center bg-[#2a2a2a]/90 backdrop-blur-sm z-10"
                    >
                      <div class="text-center space-y-2">
                        <p class="text-slate-200 text-sm">{{ speckleViewerFetchError }}</p>
                        <button
                          class="px-3 py-1.5 rounded-lg bg-slate-700 text-white text-sm hover:bg-slate-600 transition-colors"
                          @click="closeSpeckleViewer"
                        >
                          Close
                        </button>
                      </div>
                    </div>

                    <SpeckleViewer
                      v-if="selectedSpeckleModel"
                      :model-url="selectedSpeckleModel.url"
                      :model-name="selectedSpeckleModel.name"
                      :model-subtitle="selectedSpeckleModel.projectName"
                      :visible="true"
                      height="100%"
                      :server-url="config.public.speckleUrl"
                      :token="config.public.speckleToken"
                      class="viewer-canvas"
                      @close="closeSpeckleViewer"
                    />
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div v-else-if="activePage === 'settings'" class="flex-1 min-h-0 overflow-hidden">
            <SettingsView />
          </div>

          <div v-else-if="activePage === 'work'" class="flex-1 min-h-0 overflow-hidden">
            <WorkView />
          </div>

          <div v-else-if="activePage === 'timesheet'" class="flex-1 min-h-0 overflow-hidden">
            <TimesheetView :initial-section="timesheetSection" />
          </div>

          <div v-else-if="activePage === 'todo'" class="flex-1 min-h-0 overflow-hidden">
            <TodoListView />
          </div>

          <div v-else-if="activePage === 'discussion'" class="flex-1 min-h-0 overflow-hidden">
            <DiscussionView />
          </div>
        </div>
      </main>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept="image/*"
        multiple
        @change="handleFileChange"
      />
    </div>
    <div
      v-if="deleteDialog.open && deleteTarget"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
    >
      <div class="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
        <div class="space-y-2">
          <p class="text-2xl font-semibold text-white">Delete chat?</p>
          <p class="text-sm text-white/75">
            This will delete <span class="font-semibold text-white">{{ deleteTarget.title }}</span>.
          </p>
          <p v-if="!canDeleteTarget" class="text-xs text-red-300">At least one conversation must remain.</p>
        </div>
        <div class="flex justify-end gap-2">
          <button
            class="px-4 py-2 rounded-full bg-white/5 border border-white/15 text-white/85 hover:bg-white/10 transition"
            @click="closeDeleteDialog"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 rounded-full bg-red-600 text-white font-semibold hover:bg-red-700 transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!canDeleteTarget"
            @click="performDeleteConversation"
          >
            Delete
                            </button>
                          </div>
                        </div>
                        <div v-if="attachments.length" class="flex flex-wrap gap-2.5 pl-12">
                          <AttachmentChip
                            v-for="(file, idx) in attachments"
                            :key="file.name + idx"
                            :file="file"
                            @remove="removeAttachment(idx)"
                          />
                        </div>
                        </div>

  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import FolderIcon from '~/components/icons/FolderIcon.vue'
import ChatIcon from '~/components/icons/ChatIcon.vue'
import GearIcon from '~/components/icons/GearIcon.vue'
import ClockIcon from '~/components/icons/ClockIcon.vue'
import ClipboardIcon from '~/components/icons/ClipboardIcon.vue'
import WorkView from '~/components/views/WorkView.vue'
import TimesheetView from '~/components/views/TimesheetView.vue'
import TodoListView from '~/components/views/TodoListView.vue'
import DiscussionView from '~/components/views/DiscussionView.vue'
import SettingsView from '~/components/views/SettingsView.vue'
import SpeckleViewer from '~/components/SpeckleViewer.vue'
import { useChat } from '~/composables/useChat'
// Removed useSmartChat - using streaming endpoint only to avoid duplication
import { useMessageFormatter } from '~/composables/useMessageFormatter'
import { useSpeckle } from '~/composables/useSpeckle'
import { useWorkspace } from '~/composables/useWorkspace'
import { useRuntimeConfig } from '#app'
import type { Component } from 'vue'

type ChatEntry = {
  role: 'user' | 'assistant'
  content: string
  attachments?: string[]
  timestamp?: number
  liked?: boolean
  disliked?: boolean
}

type Conversation = {
  id: string
  title: string
  short: string
  time: string
  section: string
  sessionId: string
  chatLog: ChatEntry[]
  autoTitleGenerated?: boolean
  userRenamed?: boolean
}

const PAGE_IDS = ['home', 'settings', 'work', 'timesheet', 'todo', 'discussion'] as const
type ActivePage = (typeof PAGE_IDS)[number]
const TIMESHEET_SECTIONS = ['employees', 'projects', 'projectInsights', 'employeeInsights', 'nonDigital', 'settings'] as const
type TimesheetSection = (typeof TIMESHEET_SECTIONS)[number]

const STORAGE_KEY = 'workspace-memory-v1'
const GENERIC_TITLE_PREFIX = 'New Agent'
const AUTO_TITLE_MAX_LENGTH = 50

const WorkIcon = defineComponent({
  name: 'WorkGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
        h('rect', { x: '4', y: '7', width: '16', height: '11', rx: '2' }),
        h('path', { d: 'M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2' })
      ])
  }
})

const TodoIcon = defineComponent({
  name: 'TodoGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
        h('rect', { x: '4', y: '4', width: '16', height: '16', rx: '2' }),
        h('path', { d: 'M8 12l3 3 5-6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
      ])
  }
})

const UsersIcon = defineComponent({
  name: 'UsersGlyph',
  setup() {
    return () =>
      h(
        'svg',
        { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' },
        [
          h('path', { d: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2' }),
          h('circle', { cx: '9', cy: '7', r: '4' }),
          h('path', { d: 'M22 21v-2a4 4 0 0 0-3-3.87' }),
          h('path', { d: 'M16 3.13a4 4 0 0 1 0 7.75' })
        ]
      )
  }
})

const ChartIcon = defineComponent({
  name: 'ChartGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
        h('path', { d: 'M3 3v18h18' }),
        h('path', { d: 'M7 14l4-4 3 3 5-6' }),
        h('circle', { cx: '7', cy: '14', r: '1' }),
        h('circle', { cx: '11', cy: '10', r: '1' }),
        h('circle', { cx: '14', cy: '13', r: '1' }),
        h('circle', { cx: '19', cy: '7', r: '1' })
      ])
  }
})

const PersonChartIcon = defineComponent({
  name: 'PersonChartGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
        h('circle', { cx: '12', cy: '7', r: '3' }),
        h('path', { d: 'M6 21v-1a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v1' }),
        h('path', { d: 'M3 12h2' }),
        h('path', { d: 'M3 16h3' }),
        h('path', { d: 'M3 20h4' })
      ])
  }
})

const AttachmentChip = defineComponent({
  name: 'AttachmentChip',
  props: {
    file: {
      type: Object as () => { name: string; base64: string },
      required: true
    }
  },
  emits: ['remove'],
  setup(props, { emit }) {
    const isImage = computed(() => isImageFile(props.file.name))
    const imageError = ref(false)
    const ext = computed(() => getFileExtension(props.file.name))
    const sizeLabel = computed(() => formatBase64Size(props.file.base64))
    const shouldShowThumb = computed(() => isImage.value && !!props.file.base64 && !imageError.value)

    return () =>
      h(
        'div',
        {
          class:
            'group flex items-center gap-3 min-w-0 pl-3 pr-2.5 py-2 rounded-xl border border-white/10 bg-[#202020] text-white/85 transition hover:bg-white/5 hover:border-white/18 shadow-[0_6px_14px_rgba(0,0,0,0.28)]'
        },
        [
          h(
            'div',
            { class: 'w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden shrink-0' },
            [
              shouldShowThumb.value
                ? h('img', {
                    src: `data:image/*;base64,${props.file.base64}`,
                    alt: '',
                    class: 'w-full h-full object-cover',
                    onError: () => (imageError.value = true)
                  })
                : h(
                    'div',
                    { class: 'flex items-center justify-center w-full h-full text-white/75 text-[11px] font-medium' },
                    ext.value ? ext.value.toUpperCase() : 'FILE'
                  )
            ]
          ),
          h('div', { class: 'flex-1 min-w-0 space-y-0.5' }, [
            h(
              'p',
              { class: 'text-[13px] font-medium truncate', title: props.file.name },
              props.file.name
            ),
            h(
              'p',
              { class: 'text-[11px] text-white/55 uppercase tracking-wide truncate' },
              sizeLabel.value || (ext.value || 'File')
            )
          ]),
          h(
            'button',
            {
              class:
                'w-8 h-8 rounded-full flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/30 transition',
              'aria-label': `Remove ${props.file.name}`,
              onClick: () => emit('remove')
            },
            '×'
          )
        ]
      )
  }
})

const TimelineMenuItem = defineComponent({
  name: 'TimelineMenuItem',
  props: {
    icon: {
      type: Object as () => Component,
      required: true
    },
    label: {
      type: String,
      required: true
    },
    active: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { slots, emit }) {
    const IconComp = props.icon
    return () =>
      h(
        'button',
        {
          class: [
            'w-full relative flex items-center gap-3 px-3 py-2 rounded-lg text-left text-[12px] transition-colors duration-150 cursor-pointer',
            props.active ? 'bg-white/10 text-white' : 'text-white/75 hover:bg-white/6'
          ],
          onClick: (e: MouseEvent) => emit('click', e)
        },
        [
          props.active
            ? h('span', { class: 'absolute left-0 top-1 bottom-1 w-[3px] rounded-full bg-purple-500/80' })
            : null,
          h('span', { class: 'flex items-center justify-center w-7 shrink-0' }, [h(IconComp, { class: 'w-5 h-5' })]),
          h('span', { class: 'leading-[15px]' }, slots.default ? slots.default() : props.label)
        ]
      )
  }
})

const railIcons = [
  { id: 'home', component: FolderIcon, label: 'Home' },
  { id: 'work', component: WorkIcon, label: 'Work' },
  { id: 'timesheet', component: ClockIcon, label: 'Timeline' },
  { id: 'todo', component: TodoIcon, label: 'To-Do List' },
  { id: 'discussion', component: ChatIcon, label: 'Discussion' },
  { id: 'settings', component: GearIcon, label: 'Settings' }
]

const sidebarActions: Array<{ id: 'logs' | 'history' | 'docs'; label: string; component: Component }> = [
  { id: 'logs', label: 'Logs', component: ClockIcon },
  { id: 'history', label: 'Chat History', component: ChatIcon },
  { id: 'docs', label: 'Docs', component: ClipboardIcon }
]
type SidebarMode = 'history' | 'logs' | 'docs'
const sidebarMode = ref<SidebarMode>('history')

const availableModels = ['gpt-4o-120b', 'gpt-4o-mini']
const selectedModel = ref(availableModels[0])
const activePage = ref<ActivePage>('home')
const activeRail = computed(() => {
  return railIcons.some(icon => icon.id === activePage.value) ? activePage.value : 'home'
})
const userName = 'Zaryab'
const greetingTime = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Morning'
  if (hour < 18) return 'Afternoon'
  return 'Evening'
})
const greetingMessage = computed(() => `${greetingTime.value}, ${userName}`)
const route = useRoute()
const router = useRouter()
const timesheetSection = ref<TimesheetSection>('employees')
const timesheetMenuOpen = ref(false)
let timesheetMenuTimer: ReturnType<typeof setTimeout> | null = null
const hoveredSimpleMenu = ref<string | null>(null)
let simpleMenuTimer: ReturnType<typeof setTimeout> | null = null
const renamingConversationId = ref<string | null>(null)
const renameDraft = ref('')
const renameInputRefs: Record<string, HTMLInputElement | null> = {}
const timesheetMenuItems = [
  { id: 'employees', label: 'Employees', component: UsersIcon },
  { id: 'projects', label: 'Projects', component: FolderIcon },
  { id: 'projectInsights', label: 'Project Insights', component: ChartIcon },
  { id: 'employeeInsights', label: 'Employee Insights', component: PersonChartIcon },
  { id: 'nonDigital', label: 'Daily Tasks', component: TodoIcon },
  { id: 'settings', label: 'Settings', component: GearIcon }
] as const satisfies { id: TimesheetSection; label: string; component: Component }[]
const search = ref('')
const prompt = ref('')
const promptInput = ref<HTMLTextAreaElement | null>(null)
const tags = ref(['missile.ai'])
const chatContainer = ref<HTMLElement | null>(null)
const isSending = ref(false)
const attachments = ref<{ name: string; base64: string }[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const contextMenuRef = ref<HTMLElement | null>(null)
const { formatMessageText } = useMessageFormatter()
const { sendChatMessage, sendChatMessageStream } = useChat()
const { findProjectByKey, getProjectModels } = useSpeckle()
const workspace = useWorkspace()
const config = useRuntimeConfig()
type DataSources = { project_db: boolean; code_db: boolean; coop_manual: boolean }
const dataSources = ref<DataSources>({
  project_db: true,
  code_db: true,
  coop_manual: true
})
const iconRailWidth = 48 // tailwind w-12 (3rem)
const collapsedRailOffset = 10
const sidebarWidth = ref(224) // default 14rem
const minSidebarWidth = 240
const maxSidebarWidth = 340
const isSidebarCollapsed = ref(true)
const isResizingSidebar = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(0)
const sidebarRailStyle = computed(() => ({
  left: `${iconRailWidth + (isSidebarCollapsed.value ? collapsedRailOffset : sidebarWidth.value)}px`,
  top: '50%',
  transform: 'translate(-50%, -50%)',
  zIndex: 30
}))
type AgentLog = { id: string; thinking: string; timestamp: Date; type: 'thinking' | 'action' | 'result' | 'error' }
const agentLogs = ref<AgentLog[]>([])
const logsPanelOpen = ref(false)
const logsPanelHeight = ref(320)
const logsPanelBottom = ref(0)
const logsResizeStartY = ref(0)
const logsResizeStartHeight = ref(0)
const logsDragStartY = ref(0)
const logsDragStartBottom = ref(0)
const isResizingLogs = ref(false)
const isDraggingLogs = ref(false)
const showScrollToBottom = ref(false)
const contextMenu = ref<{ visible: boolean; x: number; y: number; convId: string | null }>({
  visible: false,
  x: 0,
  y: 0,
  convId: null
})

const sidebarStyle = computed(() => ({
  width: `${sidebarWidth.value}px`,
  maxWidth: `${maxSidebarWidth}px`,
  height: 'calc(100vh - 36px)',
  maxHeight: 'calc(100vh - 36px)',
  overflowX: 'visible'
}))
const deleteDialog = ref<{ open: boolean; convId: string | null }>({
  open: false,
  convId: null
})
const titleGenerationInFlight = new Set<string>()
const isDocsCompact = computed(() => sidebarWidth.value <= 280)
function isRailActionFilled(id: SidebarMode) {
  if (id === 'logs') return agentLogs.value.length > 0
  if (id === 'docs') return docListDocs.value.length > 0
  return false
}

// Speckle document list state (inline in sidebar)
const docListOpen = ref(true)
const docListDocs = ref<any[]>([])
const docListTitle = ref('')
const docListSubtitle = ref('')

const speckleViewerModels = ref<Array<{ id: string; url: string; name: string; projectName?: string }>>([])
const speckleViewerSelectedId = ref('')
const speckleViewerPanelOpen = ref(false)
const speckleViewerFetchLoading = ref(false)
const speckleViewerFetchError = ref('')
const selectedSpeckleModel = computed(() => speckleViewerModels.value.find(model => model.id === speckleViewerSelectedId.value) || null)
const viewerSplitPercent = ref(50)
const isResizingViewer = ref(false)
const viewerSplitContainer = ref<HTMLElement | null>(null)
const viewerResizeStartX = ref(0)
const viewerResizeStartPercent = ref(50)
const showSpeckleViewer = computed(() => speckleViewerPanelOpen.value && !!selectedSpeckleModel.value)
const chatPaneStyle = computed(() => (showSpeckleViewer.value ? { flexBasis: `${viewerSplitPercent.value}%` } : {}))
const viewerPaneStyle = computed(() => (showSpeckleViewer.value ? { flexBasis: `${100 - viewerSplitPercent.value}%` } : {}))

const defaultConversations: Conversation[] = [
  { id: 'conv-1', title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '52m ago', section: 'Today', sessionId: 'session-1', chatLog: [] },
  { id: 'conv-2', title: 'CFD Simulation Setup Review', short: 'CFD Setup Review', time: '1h ago', section: 'Today', sessionId: 'session-2', chatLog: [] },
  { id: 'conv-3', title: 'Calculating Reynolds number', short: 'Reynolds number', time: '2h ago', section: 'Today', sessionId: 'session-3', chatLog: [] },
  { id: 'conv-4', title: 'CFD Mesh Creation Request', short: 'CFD Mesh Request', time: '2h ago', section: 'Today', sessionId: 'session-4', chatLog: [] },
  { id: 'conv-5', title: 'Python Conversion: Knots to Mach', short: 'Knots to Mach', time: '3h ago', section: 'Today', sessionId: 'session-5', chatLog: [] },
  { id: 'conv-6', title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '5h ago', section: 'Today', sessionId: 'session-6', chatLog: [] },
  { id: 'conv-7', title: 'CFD Simulation for Car Model', short: 'Car CFD Sim', time: '6h ago', section: 'Today', sessionId: 'session-7', chatLog: [] },
  { id: 'conv-8', title: 'Ahmed Body Mesh Generation', short: 'Ahmed Mesh Gen', time: '6h ago', section: 'Today', sessionId: 'session-8', chatLog: [] },
  { id: 'conv-9', title: 'CFD Simulation Request follow-up', short: 'CFD follow-up', time: 'Yesterday', section: 'Yesterday', sessionId: 'session-9', chatLog: [] },
  { id: 'conv-10', title: 'Mesh Setup for Y+ Target', short: 'Y+ Target mesh', time: 'Nov 24', section: 'This Month', sessionId: 'session-10', chatLog: [] },
  { id: 'conv-11', title: 'Workspace Inquiry and Mapping', short: 'Workspace inquiry', time: 'Nov 24', section: 'This Month', sessionId: 'session-11', chatLog: [] },
  { id: 'conv-12', title: 'Available Tools Inquiry', short: 'Tools inquiry', time: 'Nov 19', section: 'This Month', sessionId: 'session-12', chatLog: [] },
  { id: 'conv-13', title: 'Mesh Setup for Geometry', short: 'Geometry mesh', time: 'Nov 19', section: 'This Month', sessionId: 'session-13', chatLog: [] },
  { id: 'conv-14', title: 'Mesh Refinement Zone Design', short: 'Refinement zone', time: 'Nov 19', section: 'This Month', sessionId: 'session-14', chatLog: [] }
]

const conversations = ref<Conversation[]>([...defaultConversations])

const sectionOrder = ['Today', 'Yesterday', 'This Month']
const activeConversationId = ref(conversations.value[0]?.id || '')

const activeConversation = computed(() => conversations.value.find(conv => conv.id === activeConversationId.value) || null)
const activeChatLog = computed(() => activeConversation.value?.chatLog ?? [])
const deleteTarget = computed(() => {
  if (!deleteDialog.value.convId) return null
  return conversations.value.find(conv => conv.id === deleteDialog.value.convId) || null
})
const canDeleteTarget = computed(() => conversations.value.length > 1)

const filteredConversationSections = computed(() => {
  const term = search.value.trim().toLowerCase()
  const filtered = conversations.value.filter(conv => {
    if (!term) return true
    return conv.title.toLowerCase().includes(term) || conv.short.toLowerCase().includes(term)
  })

  return sectionOrder
    .map(section => ({
      title: section,
      items: filtered.filter(conv => conv.section === section)
    }))
    .filter(section => section.items.length)
})


function scrollToBottom(smooth = false) {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
    }
  })
}

function formatEntryTime(entry: ChatEntry) {
  if (!entry.timestamp) return ''
  return new Date(entry.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function getPlainTextContent(html: string) {
  if (typeof document === 'undefined') return html
  const container = document.createElement('div')
  container.innerHTML = html.replace(/<br\s*\/?>/gi, '\n')
  const text = container.innerText || container.textContent || html
  return text.replace(/\n{3,}/g, '\n\n').trim()
}

function copyEntry(entry: ChatEntry) {
  const textToCopy = getPlainTextContent(entry.content)
  if (typeof navigator === 'undefined' || !navigator.clipboard?.writeText) return
  navigator.clipboard.writeText(textToCopy).catch(err => console.warn('Copy failed', err))
}

function editEntry(entry: ChatEntry) {
  prompt.value = entry.content
  nextTick(() => promptInput.value?.focus())
}

function resendEntry(entry: ChatEntry) {
  prompt.value = entry.content
  attachments.value = []
  handleSend()
}

function retryAssistant(index: number) {
  const conversation = activeConversation.value
  if (!conversation) return
  const entry = conversation.chatLog[index]
  if (!entry || entry.role !== 'assistant') return

  // Find the most recent user message before this assistant reply
  const priorUser = [...conversation.chatLog]
    .slice(0, index)
    .reverse()
    .find(e => e.role === 'user')

  // Remove the assistant reply we're retrying
  conversation.chatLog.splice(index, 1)

  if (priorUser) {
    regenerateAssistant(priorUser.content, conversation.sessionId)
  }
}

function toggleLike(entry: ChatEntry) {
  if (entry.disliked) entry.disliked = false
  entry.liked = !entry.liked
}

function toggleDislike(entry: ChatEntry) {
  if (entry.liked) entry.liked = false
  entry.disliked = !entry.disliked
}

function handleChatScroll() {
  const el = chatContainer.value
  if (!el) return
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollToBottom.value = distanceFromBottom > 180
}

function saveMemory() {
  if (typeof window === 'undefined') return
  try {
    const payload = {
      conversations: conversations.value,
      activeConversationId: activeConversationId.value,
      tags: tags.value,
      selectedModel: selectedModel.value,
      dataSources: dataSources.value,
      activePage: activePage.value,
      timesheetSection: timesheetSection.value,
      agentLogs: agentLogs.value,
      logsPanelOpen: logsPanelOpen.value,
      logsPanelHeight: logsPanelHeight.value,
      logsPanelBottom: logsPanelBottom.value,
      docListDocs: docListDocs.value,
      docListTitle: docListTitle.value,
      docListSubtitle: docListSubtitle.value,
      docListOpen: docListOpen.value,
      sidebarCollapsed: isSidebarCollapsed.value
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch (error) {
    console.warn('Unable to save workspace memory', error)
  }
}

function loadMemory() {
  if (typeof window === 'undefined') return
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed.conversations)) {
      conversations.value = parsed.conversations
    }
    if (parsed.activeConversationId) {
      activeConversationId.value = parsed.activeConversationId
    }
    if (Array.isArray(parsed.tags)) {
      tags.value = parsed.tags
    }
    if (typeof parsed.selectedModel === 'string' && availableModels.includes(parsed.selectedModel)) {
      selectedModel.value = parsed.selectedModel
    }
    if (parsed.dataSources) {
      dataSources.value = {
        project_db: parsed.dataSources.project_db ?? true,
        code_db: parsed.dataSources.code_db ?? true,
        coop_manual: parsed.dataSources.coop_manual ?? true
      }
    }
    if (isActivePage(parsed.activePage)) {
      activePage.value = parsed.activePage
    }
    if (isTimesheetSection(parsed.timesheetSection)) {
      timesheetSection.value = parsed.timesheetSection
    }
    if (Array.isArray(parsed.agentLogs)) {
      agentLogs.value = parsed.agentLogs.map((log: any) => ({
        id: log.id,
        thinking: log.thinking,
        timestamp: log.timestamp ? new Date(log.timestamp) : new Date(),
        type: log.type || 'thinking'
      }))
    }
    if (typeof parsed.logsPanelOpen === 'boolean') {
      logsPanelOpen.value = parsed.logsPanelOpen
    }
    if (typeof parsed.logsPanelHeight === 'number') {
      logsPanelHeight.value = parsed.logsPanelHeight
    }
    if (typeof parsed.logsPanelBottom === 'number') {
      logsPanelBottom.value = parsed.logsPanelBottom
    }
    if (Array.isArray(parsed.docListDocs)) {
      docListDocs.value = parsed.docListDocs
    }
    if (typeof parsed.docListTitle === 'string') {
      docListTitle.value = parsed.docListTitle
    }
    if (typeof parsed.docListSubtitle === 'string') {
      docListSubtitle.value = parsed.docListSubtitle
    }
    if (typeof parsed.docListOpen === 'boolean') {
      docListOpen.value = parsed.docListOpen
    }
    if (typeof parsed.sidebarCollapsed === 'boolean') {
      isSidebarCollapsed.value = parsed.sidebarCollapsed
    }
    const hasActive = conversations.value.some(conv => conv.id === activeConversationId.value)
    if (!hasActive) {
      activeConversationId.value = conversations.value[0]?.id || ''
    }
    if (!conversations.value.length) {
      conversations.value = [...defaultConversations]
      activeConversationId.value = conversations.value[0]?.id || ''
    }
  } catch (error) {
    console.warn('Unable to load workspace memory, using defaults', error)
  }
}

watch(
  () => activeChatLog.value.length,
  () => {
    scrollToBottom()
  }
)

watch(activeConversationId, () => {
  prompt.value = ''
  attachments.value = []
  nextTick(resizePrompt)
  scrollToBottom()
})

onMounted(() => {
  loadMemory()
  hydrateFromRoute()
  ensureLandingNewConversation()
  chatContainer.value?.addEventListener('scroll', handleChatScroll)
  handleChatScroll()
  document.addEventListener('click', handleGlobalClick)
  window.addEventListener('mouseup', stopSidebarResize)
  window.addEventListener('mouseup', stopViewerResize)
  nextTick(resizePrompt)
})

watch(
  [
    conversations,
    activeConversationId,
    tags,
    selectedModel,
    dataSources,
    activePage,
    timesheetSection,
    agentLogs,
    docListDocs,
    docListTitle,
    docListSubtitle,
    docListOpen,
    isSidebarCollapsed
  ],
  () => saveMemory(),
  { deep: true }
)

watch(prompt, () => {
  nextTick(resizePrompt)
})

watch(
  () => docListDocs.value.length,
  newLen => {
    if (newLen > 0) docListOpen.value = true
  }
)

watch(
  () => [route.query.page, route.query.section],
  () => hydrateFromRoute()
)

onBeforeUnmount(() => {
  chatContainer.value?.removeEventListener('scroll', handleChatScroll)
  document.removeEventListener('click', handleGlobalClick)
  window.removeEventListener('mousemove', onSidebarResize)
  window.removeEventListener('mousemove', onViewerResize)
  window.removeEventListener('mouseup', stopSidebarResize)
  window.removeEventListener('mouseup', stopViewerResize)
})

function normalizeQueryParam(value: unknown) {
  if (Array.isArray(value)) return value[0] ?? null
  return typeof value === 'string' ? value : null
}

function isActivePage(value: unknown): value is ActivePage {
  return typeof value === 'string' && PAGE_IDS.includes(value as ActivePage)
}

function isTimesheetSection(value: unknown): value is TimesheetSection {
  return typeof value === 'string' && TIMESHEET_SECTIONS.includes(value as TimesheetSection)
}

function syncRouteToPage(page: ActivePage, section?: TimesheetSection) {
  const nextQuery = { ...route.query }
  if (page === 'home') {
    delete nextQuery.page
  } else {
    nextQuery.page = page
  }
  if (page === 'timesheet') {
    nextQuery.section = section || timesheetSection.value
  } else {
    delete nextQuery.section
  }
  router.replace({ query: nextQuery })
}

function toggleSidebarCollapsed(force?: boolean) {
  isSidebarCollapsed.value = typeof force === 'boolean' ? force : !isSidebarCollapsed.value
}

function setActivePage(id: string, options?: { section?: TimesheetSection; fromRoute?: boolean }) {
  const nextPage: ActivePage = isActivePage(id) ? id : 'home'
  activePage.value = nextPage
  timesheetMenuOpen.value = false

  if (nextPage === 'timesheet' && options?.section) {
    timesheetSection.value = options.section
  }

  if (!options?.fromRoute) {
    syncRouteToPage(nextPage, options?.section)
  }
}

function setActiveRail(id: string) {
  setActivePage(id)
}

function handleSidebarAction(id: SidebarMode) {
  const isSameAction = sidebarMode.value === id && !isSidebarCollapsed.value
  if (isSameAction) {
    isSidebarCollapsed.value = true
    return
  }

  sidebarMode.value = id
  isSidebarCollapsed.value = false
  if (id === 'logs') logsPanelOpen.value = true
}

function startSidebarResize(e: MouseEvent) {
  isResizingSidebar.value = true
  resizeStartX.value = e.clientX
  resizeStartWidth.value = sidebarWidth.value
  window.addEventListener('mousemove', onSidebarResize)
  window.addEventListener('mouseup', stopSidebarResize)
}

function startLogsResize(e: MouseEvent) {
  isResizingLogs.value = true
  logsResizeStartY.value = e.clientY
  logsResizeStartHeight.value = logsPanelHeight.value
  window.addEventListener('mousemove', onLogsResize)
  window.addEventListener('mouseup', stopLogsInteractions)
}

function onLogsResize(e: MouseEvent) {
  if (!isResizingLogs.value) return
  const delta = logsResizeStartY.value - e.clientY
  const maxHeight = window.innerHeight - logsPanelBottom.value - 20
  logsPanelHeight.value = Math.max(200, Math.min(maxHeight, logsResizeStartHeight.value + delta))
}

function startLogsDrag(e: MouseEvent) {
  isDraggingLogs.value = true
  logsDragStartY.value = e.clientY
  logsDragStartBottom.value = logsPanelBottom.value
  window.addEventListener('mousemove', onLogsDrag)
  window.addEventListener('mouseup', stopLogsInteractions)
}

function onLogsDrag(e: MouseEvent) {
  if (!isDraggingLogs.value) return
  const delta = logsDragStartY.value - e.clientY
  const maxBottom = Math.max(0, window.innerHeight - logsPanelHeight.value - 50)
  logsPanelBottom.value = Math.max(0, Math.min(maxBottom, logsDragStartBottom.value + delta))
}

function stopLogsInteractions() {
  isResizingLogs.value = false
  isDraggingLogs.value = false
  window.removeEventListener('mousemove', onLogsResize)
  window.removeEventListener('mousemove', onLogsDrag)
  window.removeEventListener('mouseup', stopLogsInteractions)
}

function onSidebarResize(e: MouseEvent) {
  if (!isResizingSidebar.value) return
  const delta = e.clientX - resizeStartX.value
  const nextWidth = Math.min(maxSidebarWidth, Math.max(minSidebarWidth, resizeStartWidth.value + delta))
  sidebarWidth.value = nextWidth
}

function stopSidebarResize() {
  if (!isResizingSidebar.value) return
  isResizingSidebar.value = false
  window.removeEventListener('mousemove', onSidebarResize)
  window.removeEventListener('mouseup', stopSidebarResize)
}

function startViewerResize(e: MouseEvent) {
  if (!showSpeckleViewer.value) return
  isResizingViewer.value = true
  viewerResizeStartX.value = e.clientX
  viewerResizeStartPercent.value = viewerSplitPercent.value
  window.addEventListener('mousemove', onViewerResize)
  window.addEventListener('mouseup', stopViewerResize)
}

function onViewerResize(e: MouseEvent) {
  if (!isResizingViewer.value) return
  const container = viewerSplitContainer.value
  if (!container) return

  const rect = container.getBoundingClientRect()
  const delta = e.clientX - viewerResizeStartX.value
  const percentDelta = (delta / rect.width) * 100
  const percent = viewerResizeStartPercent.value + percentDelta
  const clamped = Math.min(70, Math.max(30, percent))
  viewerSplitPercent.value = clamped
}

function stopViewerResize() {
  if (!isResizingViewer.value) return
  isResizingViewer.value = false
  window.removeEventListener('mousemove', onViewerResize)
  window.removeEventListener('mouseup', stopViewerResize)
}

function openTimesheetMenu() {
  if (timesheetMenuTimer) clearTimeout(timesheetMenuTimer)
  timesheetMenuOpen.value = true
}

function closeTimesheetMenu() {
  if (timesheetMenuTimer) clearTimeout(timesheetMenuTimer)
  timesheetMenuTimer = setTimeout(() => {
    timesheetMenuOpen.value = false
  }, 120)
}

function handleTimesheetNav(section: TimesheetSection) {
  timesheetSection.value = section
  setActivePage('timesheet', { section })
  timesheetMenuOpen.value = false
}

function hydrateFromRoute() {
  const pageFromRoute = normalizeQueryParam(route.query.page)
  if (!pageFromRoute || !isActivePage(pageFromRoute)) return

  const sectionFromRoute =
    pageFromRoute === 'timesheet' ? normalizeQueryParam(route.query.section) : null
  const resolvedSection =
    pageFromRoute === 'timesheet' && sectionFromRoute && isTimesheetSection(sectionFromRoute)
      ? sectionFromRoute
      : undefined

  setActivePage(pageFromRoute, { section: resolvedSection, fromRoute: true })
}

function showSimpleMenu(id: string) {
  if (simpleMenuTimer) clearTimeout(simpleMenuTimer)
  hoveredSimpleMenu.value = id
}

function hideSimpleMenu() {
  if (simpleMenuTimer) clearTimeout(simpleMenuTimer)
  simpleMenuTimer = setTimeout(() => {
    hoveredSimpleMenu.value = null
  }, 120)
}

function setRenameInputRef(id: string, el: HTMLInputElement | null) {
  if (!el) {
    delete renameInputRefs[id]
  } else {
    renameInputRefs[id] = el
  }
}

function startRename(convId: string) {
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return
  renamingConversationId.value = convId
  renameDraft.value = convo.title
  closeContextMenu()
  nextTick(() => {
    renameInputRefs[convId]?.focus()
    renameInputRefs[convId]?.select()
  })
}

function cancelRename() {
  renamingConversationId.value = null
  renameDraft.value = ''
}

function confirmRename(convId: string) {
  if (renamingConversationId.value !== convId) return
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return cancelRename()
  const newTitle = renameDraft.value.trim()
  if (!newTitle || newTitle === convo.title) return cancelRename()
  convo.title = newTitle
  convo.short = shortenTitle(newTitle)
  convo.time = 'Just now'
  convo.userRenamed = true
  convo.autoTitleGenerated = true
  touchConversation(convo.id)
  cancelRename()
}

function formatTimestamp(ts: Date | number | string) {
  const d = ts instanceof Date ? ts : new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatThinking(text: string): string {
  if (!text) return ''
  let html = text
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-white mt-4 mb-2">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-white mt-5 mb-3">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-semibold text-white mt-6 mb-4">$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
    .replace(/^[-*] (.*$)/gim, '<li class="ml-4 mb-1 text-white/80">$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li class="ml-4 mb-1 text-white/80">$1</li>')
    .replace(/\n\n/g, '</p><p class="mb-3 leading-relaxed text-white/85">')
    .replace(/\n/g, '<br>')

  html = html.replace(/(<li.*<\/li>)/gs, '<ul class="list-disc list-inside space-y-1 my-3 ml-4">$1</ul>')

  if (!html.startsWith('<')) {
    html = '<p class="mb-3 leading-relaxed text-white/85">' + html + '</p>'
  } else if (!html.includes('<p')) {
    html = '<p class="mb-3 leading-relaxed text-white/85">' + html + '</p>'
  }

  return html
}

function startNewConversation() {
  const newId = `conv-${Date.now()}`
  const title = `${GENERIC_TITLE_PREFIX} ${conversations.value.length + 1}`
  const newConversation: Conversation = {
    id: newId,
    title,
    short: shortenTitle(title),
    time: 'Just now',
    section: 'Today',
    sessionId: newId,
    chatLog: [],
    autoTitleGenerated: false,
    userRenamed: false
  }
  conversations.value = [newConversation, ...conversations.value]
  activeConversationId.value = newId
  setActivePage('home')
  prompt.value = ''
  attachments.value = []
}

function ensureLandingNewConversation() {
  const pageFromRoute = normalizeQueryParam(route.query.page)
  if (pageFromRoute && pageFromRoute !== 'home') return

  startNewConversation()

  const currentId = activeConversationId.value
  conversations.value = conversations.value.filter(conv => {
    if (conv.id === currentId) return true
    const isEmptyGeneric = conv.chatLog.length === 0 && isGenericTitle(conv.title)
    return !isEmptyGeneric
  })
}

function selectConversation(id: string) {
  if (activeConversationId.value === id) return
  activeConversationId.value = id
  setActivePage('home')
  prompt.value = ''
  closeContextMenu()
}

function handleTagClick(tag: string) {
  prompt.value = tag
}

function removeTag(tag: string) {
  tags.value = tags.value.filter(t => t !== tag)
}

function getFileExtension(name: string) {
  const parts = name.split('.')
  if (parts.length <= 1) return ''
  return parts.pop()?.toLowerCase() || ''
}

function isImageFile(name: string) {
  return /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(name)
}

function formatBase64Size(base64: string) {
  if (!base64) return ''
  const padding = (base64.match(/=+$/)?.[0].length ?? 0)
  const bytes = Math.max(0, Math.floor((base64.length * 3) / 4 - padding))
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function openFilePicker() {
  fileInput.value?.click()
}

function shortenTitle(title: string) {
  return title.length > 26 ? `${title.slice(0, 23)}...` : title
}

function isGenericTitle(title: string) {
  if (!title) return true
  const normalized = title.trim().toLowerCase()
  const generic = GENERIC_TITLE_PREFIX.toLowerCase()
  return normalized === generic || normalized.startsWith(`${generic} `) || normalized === 'untitled'
}

function normalizeTitleSource(text: string) {
  return text.replace(/\s+/g, ' ').trim()
}

function isMeaningfulTitleSource(text: string) {
  const cleaned = normalizeTitleSource(text)
  if (!cleaned) return false
  const words = cleaned.split(' ')
  return cleaned.length >= 8 || words.length >= 3
}

function truncateForPrompt(text: string, limit = 320) {
  if (!text) return ''
  const trimmed = normalizeTitleSource(text)
  return trimmed.length > limit ? `${trimmed.slice(0, limit)}...` : trimmed
}

function buildTitlePrompt(question: string, answer?: string) {
  const parts = [
    'Generate a concise conversation title (3-7 words, max 50 characters).',
    'Prefer key project numbers if they exist. Respond with the title only.',
    `Question: ${truncateForPrompt(question)}`
  ]

  if (answer) {
    parts.push(`Assistant: ${truncateForPrompt(answer)}`)
  }

  return parts.join('\n')
}

function sanitizeGeneratedTitle(raw: string) {
  if (!raw) return ''
  const firstLine = raw.split(/\r?\n/)[0]
  const cleaned = firstLine
    .replace(/^["'\s]+|["'\s]+$/g, '')
    .replace(/^title[:\-]?\s*/i, '')
    .trim()

  if (!cleaned) return ''
  return cleaned.length > AUTO_TITLE_MAX_LENGTH
    ? cleaned.slice(0, AUTO_TITLE_MAX_LENGTH).trim()
    : cleaned
}

function getFirstUserMessageText(conversation: Conversation) {
  const firstUser = conversation.chatLog.find(entry => entry.role === 'user')
  return normalizeTitleSource(firstUser?.content || '')
}

function pickTitleQuestion(conversation: Conversation, latestUserMessage: string) {
  const firstUserQuestion = getFirstUserMessageText(conversation)
  if (isMeaningfulTitleSource(firstUserQuestion)) return firstUserQuestion

  const latest = normalizeTitleSource(latestUserMessage)
  if (isMeaningfulTitleSource(latest)) return latest

  return ''
}

async function maybeGenerateTitle(conversation: Conversation | null, latestUserMessage: string, assistantReply?: string) {
  if (!conversation) return
  if (conversation.userRenamed) return
  if (conversation.autoTitleGenerated) return
  if (!isGenericTitle(conversation.title)) return
  if (!conversation.chatLog.some(entry => entry.role === 'user')) return

  const titleQuestion = pickTitleQuestion(conversation, latestUserMessage)
  if (!titleQuestion) return

  if (titleGenerationInFlight.has(conversation.id)) return
  titleGenerationInFlight.add(conversation.id)

  try {
    const prompt = buildTitlePrompt(titleQuestion, assistantReply)
    const response = await sendChatMessage(
      prompt,
      `${conversation.sessionId}-title`,
      undefined,
      { project_db: false, code_db: false, coop_manual: false }
    )
    const generated = sanitizeGeneratedTitle(response.reply || response.message || '')
    if (!generated) return

    conversation.title = generated
    conversation.short = shortenTitle(generated)
    conversation.autoTitleGenerated = true
    conversation.time = 'Just now'
    touchConversation(conversation.id)
  } catch (error) {
    console.warn('Auto-title generation failed', error)
  } finally {
    titleGenerationInFlight.delete(conversation.id)
  }
}

function convertFileToBase64(file: File): Promise<{ name: string; base64: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      const base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
      resolve({ name: file.name, base64 })
    }
    reader.onerror = () => reject(new Error('Unable to read file'))
    reader.readAsDataURL(file)
  })
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (!files.length) return

  try {
    const converted = await Promise.all(files.map(file => convertFileToBase64(file)))
    attachments.value.push(...converted)
  } catch (error) {
    console.error('Failed to read attachments', error)
  } finally {
    // Allow selecting the same file again later
    target.value = ''
  }
}

function removeAttachment(idx: number) {
  attachments.value.splice(idx, 1)
}

function toggleDataSource(key: keyof DataSources) {
  dataSources.value[key] = !dataSources.value[key]
}

// Recreate SmartChatPanel's document list + Speckle modal wiring
function openDocumentsList(documents: any[], title?: string, subtitle?: string) {
  docListDocs.value = documents
  docListTitle.value = title || 'Documents'
  docListSubtitle.value = subtitle || ''
  docListOpen.value = true
}

function handleDocumentSelect(doc: any) {
  const models = docListDocs.value
    .filter(d => d.url)
    .map(d => ({
      id: d.id,
      url: d.url,
      name: d.name || d.title || 'Model',
      projectName: d.metadata?.projectName
    }))

  if (models.length) {
    // Ensure models are available for the docked viewer
    speckleViewerModels.value = models
    speckleViewerSelectedId.value = doc.id || models[0].id
    speckleViewerPanelOpen.value = true
    viewerSplitPercent.value = 50
  }
}

function closeSpeckleViewer() {
  speckleViewerPanelOpen.value = false
  speckleViewerSelectedId.value = ''
}

function openSpeckleViewerWithModels(models: Array<{ id: string; url: string; name: string; projectName?: string }>) {
  if (!models.length) return
  speckleViewerModels.value = models
  speckleViewerSelectedId.value = models[0].id
  speckleViewerPanelOpen.value = true
  viewerSplitPercent.value = 50
}

async function fetchAndDisplaySpeckleModels(answerText: string, fallbackText?: string) {
  speckleViewerFetchLoading.value = true
  speckleViewerFetchError.value = ''

  const projectKeys = new Set<string>()
  const collect = (text?: string) => {
    if (!text) return
    const regex = /\b(\d{2}-\d{2}-\d{3})\b/g
    let match
    while ((match = regex.exec(text)) !== null) {
      projectKeys.add(match[1])
    }
  }

  collect(answerText)
  collect(fallbackText)

  if (projectKeys.size === 0) {
    speckleViewerFetchLoading.value = false
    return
  }

  const modelDocuments: any[] = []

  for (const projectKey of Array.from(projectKeys)) {
    try {
      const project = await findProjectByKey(projectKey)
      if (!project) {
        console.log(`No Speckle project found for key: ${projectKey}`)
        continue
      }

      const models = await getProjectModels(project.id)
      if (models.length === 0) {
        console.log(`No models found for project ${project.name} (${projectKey})`)
        continue
      }

      for (const model of models) {
        const modelUrl = `${config.public.speckleUrl}/projects/${project.id}/models/${model.id}`
        modelDocuments.push({
          id: `speckle-${project.id}-${model.id}`,
          title: model.name,
          name: model.name,
          description: `${project.name} - ${model.name}`,
          url: modelUrl,
          metadata: {
            projectId: project.id,
            modelId: model.id,
            projectKey,
            projectName: project.name
          }
        })
      }
    } catch (error) {
      console.error(`Error fetching models for project ${projectKey}:`, error)
      speckleViewerFetchError.value = 'Unable to load 3D models right now.'
    }
  }

  if (modelDocuments.length > 0) {
    openDocumentsList(
      modelDocuments,
      '3D Models',
      'Click on a model to view it in the viewer'
    )
    const modalModels = modelDocuments.map(doc => ({
      id: doc.id,
      url: doc.url,
      name: doc.name,
      projectName: doc.metadata?.projectName as string | undefined
    }))
    openSpeckleViewerWithModels(modalModels)
  } else {
    speckleViewerModels.value = []
    speckleViewerSelectedId.value = ''
    speckleViewerPanelOpen.value = false
  }

  speckleViewerFetchLoading.value = false
}

function resizePrompt() {
  const el = promptInput.value
  if (!el) return
  const maxHeight = 48
  el.style.height = 'auto'
  const next = Math.min(el.scrollHeight, maxHeight)
  el.style.height = `${next}px`
  el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function touchConversation(convId: string) {
  const idx = conversations.value.findIndex(conv => conv.id === convId)
  if (idx === -1) return
  const [conv] = conversations.value.splice(idx, 1)
  conv.time = 'Just now'
  conv.section = 'Today'
  conversations.value = [conv, ...conversations.value]
}

function handleAgentLog(log: AgentLog) {
  const entry: AgentLog = {
    id: log.id,
    thinking: log.thinking,
    timestamp: log.timestamp ? new Date(log.timestamp) : new Date(),
    type: log.type || 'thinking'
  }
  agentLogs.value.unshift(entry)
  if (agentLogs.value.length > 50) {
    agentLogs.value = agentLogs.value.slice(0, 50)
  }
  logsPanelOpen.value = true
}

async function handleSend() {
  const hasMessage = prompt.value.trim().length > 0
  const hasAttachments = attachments.value.length > 0
  if ((!hasMessage && !hasAttachments) || isSending.value) return

  const conversation = activeConversation.value
  if (!conversation) return

  const message = hasMessage ? prompt.value.trim() : 'What is shown in these attachments?'
  const attachmentNames = attachments.value.map(file => file.name)
  const imagesBase64 = attachments.value.length ? attachments.value.map(file => file.base64) : undefined

  conversation.chatLog.push({
    role: 'user',
    content: message,
    attachments: attachmentNames.length ? attachmentNames : undefined,
    timestamp: Date.now()
  })

  prompt.value = ''
  attachments.value = []
  touchConversation(conversation.id)
  isSending.value = true
  scrollToBottom()

  try {
    // Use streaming endpoint ONLY - no duplicate calls
    let streamingMessageId: string | null = null
    let streamError: Error | null = null

    await sendChatMessageStream(
      message,
      conversation.sessionId,
      imagesBase64,
      dataSources.value,
      {
        onLog: log => {
          console.log('Thinking log:', log)
          handleAgentLog({
            id: `log-${Date.now()}`,
            thinking: log.message,
            timestamp: new Date(),
            type: 'thinking'
          })
        },
        onToken: token => {
          // Create streaming message on first token
          if (!streamingMessageId) {
            streamingMessageId = `streaming-${Date.now()}`
            conversation.chatLog.push({
              role: 'assistant',
              content: '',
              timestamp: Date.now()
            })
          }
          
          // Append token to streaming message
          const messageIndex = conversation.chatLog.length - 1
          if (messageIndex >= 0) {
            conversation.chatLog[messageIndex].content += token.content
            scrollToBottom()
          }
        },
        onComplete: async result => {
          const finalAnswer = result.reply || result.message || 'No response generated.'
          
          // Update streaming message with final answer
          if (streamingMessageId) {
            const messageIndex = conversation.chatLog.length - 1
            if (messageIndex >= 0) {
              conversation.chatLog[messageIndex].content = formatMessageText(finalAnswer)
              conversation.chatLog[messageIndex].timestamp = Date.now()
            }
          } else {
            // Fallback: create message if streaming didn't happen
            conversation.chatLog.push({ 
              role: 'assistant', 
              content: formatMessageText(finalAnswer), 
              timestamp: Date.now() 
            })
          }
          
          void maybeGenerateTitle(conversation, message, finalAnswer)
          await fetchAndDisplaySpeckleModels(finalAnswer, message)
          scrollToBottom(true)
        },
        onError: error => {
          streamError = error
        }
      }
    )

    if (streamError) {
      throw streamError
    }
  } catch (error: any) {
    console.error('Send failed', error)
    conversation.chatLog.push({ role: 'assistant', content: 'Sorry, something went wrong sending that message.' })
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

async function regenerateAssistant(message: string, sessionId: string) {
  if (isSending.value) return
  isSending.value = true
  try {
    // Use streaming endpoint ONLY - no duplicate calls
    const conversation = activeConversation.value
    if (!conversation) return
    
    let streamingMessageId: string | null = null
    let streamError: Error | null = null

    await sendChatMessageStream(
      message,
      sessionId,
      undefined,
      dataSources.value,
      {
        onLog: log => {
          handleAgentLog({
            id: `log-${Date.now()}`,
            thinking: log.message,
            timestamp: new Date(),
            type: 'thinking'
          })
        },
        onToken: token => {
          // Create streaming message on first token
          if (!streamingMessageId) {
            streamingMessageId = `streaming-${Date.now()}`
            conversation.chatLog.push({
              role: 'assistant',
              content: '',
              timestamp: Date.now()
            })
          }
          
          // Append token to streaming message
          const messageIndex = conversation.chatLog.length - 1
          if (messageIndex >= 0) {
            conversation.chatLog[messageIndex].content += token.content
            scrollToBottom()
          }
        },
        onComplete: async result => {
          const finalAnswer = result.reply || result.message || 'No response generated.'
          
          // Update streaming message with final answer
          if (streamingMessageId) {
            const messageIndex = conversation.chatLog.length - 1
            if (messageIndex >= 0) {
              conversation.chatLog[messageIndex].content = formatMessageText(finalAnswer)
              conversation.chatLog[messageIndex].timestamp = Date.now()
            }
          } else {
            // Fallback: create message if streaming didn't happen
            conversation.chatLog.push({
              role: 'assistant',
              content: formatMessageText(finalAnswer),
              timestamp: Date.now()
            })
          }
          
          void maybeGenerateTitle(conversation, message, finalAnswer)
          await fetchAndDisplaySpeckleModels(finalAnswer, message)
          scrollToBottom(true)
        },
        onError: error => {
          streamError = error
        }
      }
    )

    if (streamError) {
      throw streamError
    }
  } catch (error: any) {
    console.error('Regenerate failed', error)
    const conversation = activeConversation.value
    if (conversation) {
      conversation.chatLog.push({ role: 'assistant', content: 'Sorry, something went wrong regenerating that response.' })
    }
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

function handleUpgrade() {
  alert('Upgrade options are coming soon.')
}

function renameConversation(convId: string) {
  startRename(convId)
}

function openContextMenu(event: MouseEvent, convId: string) {
  event.stopPropagation()
  closeContextMenu()
  const parentRect = (event.currentTarget as HTMLElement).closest('aside')?.getBoundingClientRect()
  const x = parentRect ? event.clientX - parentRect.left : event.clientX
  const y = parentRect ? event.clientY - parentRect.top : event.clientY
  const menuWidth = 180
  const menuHeight = 96
  const boundsWidth = parentRect ? parentRect.width : window.innerWidth
  const boundsHeight = parentRect ? parentRect.height : window.innerHeight
  const clampedX = Math.max(8, Math.min(x, boundsWidth - menuWidth - 8))
  const clampedY = Math.max(8, Math.min(y, boundsHeight - menuHeight - 8))
  contextMenu.value = { visible: true, x: clampedX, y: clampedY, convId }
}

function closeContextMenu() {
  contextMenu.value = { visible: false, x: 0, y: 0, convId: null }
}

function handleGlobalClick(event: MouseEvent) {
  if (!contextMenu.value.visible) return
  if (event.button === 2) return
  const menuEl = contextMenuRef.value
  if (menuEl && menuEl.contains(event.target as Node)) return
  closeContextMenu()
}

function openDeleteDialog(convId: string) {
  closeContextMenu()
  deleteDialog.value = { open: true, convId }
}

function closeDeleteDialog() {
  deleteDialog.value = { open: false, convId: null }
}

function deleteConversation(convId: string) {
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return
  conversations.value = conversations.value.filter(conv => conv.id !== convId)
  if (activeConversationId.value === convId) {
    activeConversationId.value = conversations.value[0]?.id || ''
    prompt.value = ''
    attachments.value = []
  }
}

function performDeleteConversation() {
  const convId = deleteDialog.value.convId
  if (!convId) return closeDeleteDialog()
  if (!canDeleteTarget.value) {
    return closeDeleteDialog()
  }
  deleteConversation(convId)
  closeDeleteDialog()
}
</script>

<style scoped>
.custom-scroll {
  scrollbar-width: none; /* Firefox */
}
.custom-scroll::-webkit-scrollbar {
  width: 0px;
  height: 0px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: transparent;
}

.workspace-shell {
  min-width: 0;
  height: calc(100vh - 36px);
}

.workspace-root {
  font-size: 12px;
}

.workspace-main {
  min-width: 0;
}

.attachment-tray-enter-active,
.attachment-tray-leave-active {
  transition: opacity 180ms ease-out, transform 180ms ease-out;
}
.attachment-tray-enter-from,
.attachment-tray-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
.attachment-tray-enter-to,
.attachment-tray-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.conversation-sidebar {
  min-width: 200px;
}

.workspace-root {
  font-size: 11px;
  height: 100vh;
  overflow: hidden;
}

.chat-frame {
  width: min(100%, 960px);
  margin: 0 auto;
  height: 100%;
  max-height: 100%;
}

.chat-frame--docked {
  width: 100%;
  max-width: 100%;
  margin: 0;
}

.viewer-pane {
  min-width: 320px;
}

.viewer-resize-handle {
  width: 10px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
}

.viewer-resize-grip {
  height: 64px;
  width: 6px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
}

.viewer-canvas-shell {
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  padding: 0;
  height: 100%;
  min-height: 0;
}

.viewer-canvas {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  min-height: 0;
}

.viewer-close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 30;
  width: 32px;
  height: 32px;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(31, 41, 55, 0.9);
  color: #e5e7eb;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
}

.viewer-close:hover {
  background: rgba(59, 73, 92, 0.95);
  border-color: rgba(255, 255, 255, 0.28);
}

@media (max-width: 1024px) {
  .workspace-shell {
    flex-direction: column;
  }
  .conversation-sidebar {
    width: 100%;
    order: 2;
    border-right: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    max-height: 45vh;
  }
  .workspace-main {
    order: 1;
  }
}

@media (max-width: 640px) {
  .workspace-main > div {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .conversation-sidebar {
    max-height: 50vh;
  }
}

@media (min-width: 1440px) {
  .workspace-root {
    font-size: 12px;
  }
}
</style>
