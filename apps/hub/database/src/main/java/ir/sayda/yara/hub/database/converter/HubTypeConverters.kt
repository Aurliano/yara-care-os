package ir.sayda.yara.hub.database.converter

import androidx.room.TypeConverter

class HubTypeConverters {
    @TypeConverter
    fun longToNullableLong(value: Long?): Long? = value
}
