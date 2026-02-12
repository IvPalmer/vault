#!/usr/bin/env swift
/*
  reminders-helper.swift — Access Apple Reminders + Calendar via EventKit.
  Unlike osascript, EventKit can see lists/calendars inside folder groups.

  Reminders:
    ./reminders-helper lists                            — list all reminder lists
    ./reminders-helper get "R&R Tarefas"                — get incomplete reminders
    ./reminders-helper add "R&R Tarefas" "Buy milk"     — add a reminder
    ./reminders-helper complete "R&R Tarefas" "Buy milk" — complete a reminder

  Calendar:
    ./reminders-helper calendars                        — list all calendars
    ./reminders-helper events "R&R" 14                  — events from next N days (default 14)
    ./reminders-helper add-event "R&R" "Dinner" "2026-02-15T19:00" "2026-02-15T21:00"
*/

import EventKit
import Foundation

let store = EKEventStore()

// Request access to both Reminders and Calendar
let semReminders = DispatchSemaphore(value: 0)
let semEvents = DispatchSemaphore(value: 0)

if #available(macOS 14.0, *) {
    store.requestFullAccessToReminders { _, _ in semReminders.signal() }
    store.requestFullAccessToEvents { _, _ in semEvents.signal() }
} else {
    store.requestAccess(to: .reminder) { _, _ in semReminders.signal() }
    store.requestAccess(to: .event) { _, _ in semEvents.signal() }
}
semReminders.wait()
semEvents.wait()

let args = CommandLine.arguments

// ── Helpers ──────────────────────────────────────────────

func findReminderList(named name: String) -> EKCalendar? {
    return store.calendars(for: .reminder).first { $0.title == name }
}

func findEventCalendar(named name: String) -> EKCalendar? {
    return store.calendars(for: .event).first { $0.title == name }
}

func outputJSON(_ obj: Any) {
    if let data = try? JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted]),
       let str = String(data: data, encoding: .utf8) {
        print(str)
    }
}

let isoFormatter: ISO8601DateFormatter = {
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime]
    return f
}()

let localFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "yyyy-MM-dd'T'HH:mm"
    f.timeZone = TimeZone.current
    return f
}()

guard args.count >= 2 else {
    print("{\"error\": \"Usage: ./reminders-helper <command> [args...]\"}")
    exit(1)
}

let command = args[1]

switch command {

// ════════════════════════════════════════════════════════
// REMINDERS
// ════════════════════════════════════════════════════════

case "lists":
    let calendars = store.calendars(for: .reminder)
    let names = calendars.map { $0.title }
    outputJSON(["lists": names])

case "get":
    guard args.count >= 3 else {
        print("{\"error\": \"Usage: get <list_name>\"}")
        exit(1)
    }
    let listName = args[2]
    guard let cal = findReminderList(named: listName) else {
        print("{\"error\": \"List not found: \(listName)\"}")
        exit(1)
    }

    let predicate = store.predicateForIncompleteReminders(
        withDueDateStarting: nil, ending: nil, calendars: [cal]
    )

    var results: [EKReminder]?
    let fetchSem = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: predicate) { r in results = r; fetchSem.signal() }
    fetchSem.wait()

    let reminders = (results ?? []).map { r -> [String: Any] in
        var dict: [String: Any] = ["name": r.title ?? "", "priority": r.priority]
        if let due = r.dueDateComponents?.date {
            dict["due_date"] = isoFormatter.string(from: due)
        } else {
            dict["due_date"] = ""
        }
        dict["notes"] = r.notes ?? ""
        return dict
    }
    outputJSON(["list": listName, "reminders": reminders, "count": reminders.count])

case "add":
    guard args.count >= 4 else {
        print("{\"error\": \"Usage: add <list_name> <reminder_name>\"}")
        exit(1)
    }
    let listName = args[2]
    let reminderName = args[3]
    guard let cal = findReminderList(named: listName) else {
        print("{\"error\": \"List not found: \(listName)\"}")
        exit(1)
    }
    let reminder = EKReminder(eventStore: store)
    reminder.title = reminderName
    reminder.calendar = cal
    do {
        try store.save(reminder, commit: true)
        outputJSON(["ok": true, "name": reminderName, "list": listName])
    } catch {
        print("{\"error\": \"\(error.localizedDescription)\"}")
        exit(1)
    }

case "complete":
    guard args.count >= 4 else {
        print("{\"error\": \"Usage: complete <list_name> <reminder_name>\"}")
        exit(1)
    }
    let listName = args[2]
    let reminderName = args[3]
    guard let cal = findReminderList(named: listName) else {
        print("{\"error\": \"List not found: \(listName)\"}")
        exit(1)
    }
    let predicate = store.predicateForIncompleteReminders(
        withDueDateStarting: nil, ending: nil, calendars: [cal]
    )
    var results: [EKReminder]?
    let fetchSem = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: predicate) { r in results = r; fetchSem.signal() }
    fetchSem.wait()

    if let match = results?.first(where: { $0.title == reminderName }) {
        match.isCompleted = true
        do {
            try store.save(match, commit: true)
            outputJSON(["ok": true, "name": reminderName])
        } catch {
            print("{\"error\": \"\(error.localizedDescription)\"}")
            exit(1)
        }
    } else {
        print("{\"error\": \"Reminder not found\"}")
        exit(1)
    }

// ════════════════════════════════════════════════════════
// CALENDAR
// ════════════════════════════════════════════════════════

case "calendars":
    let cals = store.calendars(for: .event)
    let list = cals.map { c -> [String: Any] in
        return ["name": c.title, "source": c.source.title, "color": c.cgColor?.components?.description ?? ""]
    }
    outputJSON(["calendars": list])

case "events":
    guard args.count >= 3 else {
        print("{\"error\": \"Usage: events <calendar_name> [days]\"}")
        exit(1)
    }
    let calName = args[2]
    let days = args.count >= 4 ? (Int(args[3]) ?? 14) : 14

    guard let cal = findEventCalendar(named: calName) else {
        print("{\"error\": \"Calendar not found: \(calName)\"}")
        exit(1)
    }

    let now = Date()
    let future = Calendar.current.date(byAdding: .day, value: days, to: now)!
    let predicate = store.predicateForEvents(withStart: now, end: future, calendars: [cal])
    let events = store.events(matching: predicate)

    let eventList = events.map { e -> [String: Any] in
        var dict: [String: Any] = [
            "title": e.title ?? "",
            "start": isoFormatter.string(from: e.startDate),
            "end": isoFormatter.string(from: e.endDate),
            "all_day": e.isAllDay,
            "location": e.location ?? "",
            "notes": e.notes ?? "",
        ]
        if e.hasRecurrenceRules {
            dict["recurring"] = true
        }
        return dict
    }

    outputJSON([
        "calendar": calName,
        "days": days,
        "events": eventList,
        "count": eventList.count,
    ])

case "add-event":
    guard args.count >= 5 else {
        print("{\"error\": \"Usage: add-event <calendar_name> <title> <start> <end> [location]\"}")
        exit(1)
    }
    let calName = args[2]
    let title = args[3]
    let startStr = args[4]
    let endStr = args[5]
    let location = args.count >= 7 ? args[6] : ""

    guard let cal = findEventCalendar(named: calName) else {
        print("{\"error\": \"Calendar not found: \(calName)\"}")
        exit(1)
    }
    guard let startDate = localFormatter.date(from: startStr) else {
        print("{\"error\": \"Invalid start date format. Use yyyy-MM-ddTHH:mm\"}")
        exit(1)
    }
    guard let endDate = localFormatter.date(from: endStr) else {
        print("{\"error\": \"Invalid end date format. Use yyyy-MM-ddTHH:mm\"}")
        exit(1)
    }

    let event = EKEvent(eventStore: store)
    event.title = title
    event.startDate = startDate
    event.endDate = endDate
    event.calendar = cal
    if !location.isEmpty { event.location = location }

    do {
        try store.save(event, span: .thisEvent)
        outputJSON(["ok": true, "title": title, "calendar": calName])
    } catch {
        print("{\"error\": \"\(error.localizedDescription)\"}")
        exit(1)
    }

default:
    print("{\"error\": \"Unknown command: \(command)\"}")
    exit(1)
}
