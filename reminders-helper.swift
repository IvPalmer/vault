#!/usr/bin/env swift
/*
  reminders-helper.swift — Access Apple Reminders via EventKit.
  Unlike osascript, EventKit can see lists inside folder groups.

  Usage:
    swift reminders-helper.swift lists                  — list all reminder lists
    swift reminders-helper.swift get "R&R Tarefas"      — get incomplete reminders
    swift reminders-helper.swift add "R&R Tarefas" "Buy milk"  — add a reminder
    swift reminders-helper.swift complete "R&R Tarefas" "Buy milk" — complete a reminder
*/

import EventKit
import Foundation

let store = EKEventStore()
let semaphore = DispatchSemaphore(value: 0)

// Request access
if #available(macOS 14.0, *) {
    store.requestFullAccessToReminders { granted, error in
        semaphore.signal()
    }
} else {
    store.requestAccess(to: .reminder) { granted, error in
        semaphore.signal()
    }
}
semaphore.wait()

let args = CommandLine.arguments

func findCalendar(named name: String) -> EKCalendar? {
    let calendars = store.calendars(for: .reminder)
    return calendars.first { $0.title == name }
}

func outputJSON(_ obj: Any) {
    if let data = try? JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted]),
       let str = String(data: data, encoding: .utf8) {
        print(str)
    }
}

guard args.count >= 2 else {
    print("{\"error\": \"Usage: swift reminders-helper.swift <command> [args...]\"}")
    exit(1)
}

let command = args[1]

switch command {
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
    guard let cal = findCalendar(named: listName) else {
        print("{\"error\": \"List not found: \(listName)\"}")
        exit(1)
    }

    let predicate = store.predicateForIncompleteReminders(
        withDueDateStarting: nil, ending: nil, calendars: [cal]
    )

    var results: [EKReminder]?
    let fetchSemaphore = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: predicate) { reminders in
        results = reminders
        fetchSemaphore.signal()
    }
    fetchSemaphore.wait()

    let reminders = (results ?? []).map { r -> [String: Any] in
        var dict: [String: Any] = [
            "name": r.title ?? "",
            "priority": r.priority,
        ]
        if let due = r.dueDateComponents?.date {
            let formatter = ISO8601DateFormatter()
            dict["due_date"] = formatter.string(from: due)
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
    guard let cal = findCalendar(named: listName) else {
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
    guard let cal = findCalendar(named: listName) else {
        print("{\"error\": \"List not found: \(listName)\"}")
        exit(1)
    }

    let predicate = store.predicateForIncompleteReminders(
        withDueDateStarting: nil, ending: nil, calendars: [cal]
    )

    var results: [EKReminder]?
    let fetchSemaphore = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: predicate) { reminders in
        results = reminders
        fetchSemaphore.signal()
    }
    fetchSemaphore.wait()

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

default:
    print("{\"error\": \"Unknown command: \(command)\"}")
    exit(1)
}
