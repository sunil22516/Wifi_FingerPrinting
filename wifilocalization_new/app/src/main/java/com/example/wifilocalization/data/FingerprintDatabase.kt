package com.example.wifilocalization.data
//
//object FingerprintDatabase {
//
//    private val data = mutableListOf<Fingerprint>()
//
//    fun add(fp: Fingerprint) {
//        data.add(fp)
//    }
//
//
//    fun getAll(): List<Fingerprint> = data
//}

object FingerprintDatabase {

    private val data = mutableListOf<Fingerprint>()

    fun add(fp: Fingerprint) {
        data.add(fp)
    }

    fun getAll(): List<Fingerprint> = data

    // ✅ ADD THIS
    fun clear() {
        data.clear()
    }

    // ✅ OPTIONAL (better delete directly here)
    fun deleteByLocation(locationName: String) {
        data.removeAll {
            it.location.equals(locationName, ignoreCase = true)
        }
    }
}