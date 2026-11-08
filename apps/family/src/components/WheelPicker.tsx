import React, { useRef, useEffect } from "react";
import {
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  View,
} from "react-native";
import { AppText } from "./AppText";
import { colors, radius } from "../theme/tokens";

export interface WheelItem<T = string | number> {
  label: string;
  value: T;
}

interface Props<T> {
  items: WheelItem<T>[];
  selectedValue: T;
  onValueChange: (value: T) => void;
  itemHeight?: number;
  width?: number;
}

const DEFAULT_ITEM_HEIGHT = 44;

export function WheelPicker<T extends string | number>({
  items,
  selectedValue,
  onValueChange,
  itemHeight = DEFAULT_ITEM_HEIGHT,
  width = 90,
}: Props<T>) {
  const flatListRef = useRef<FlatList>(null);
  const selectedIndex = items.findIndex((i) => i.value === selectedValue);

  useEffect(() => {
    if (selectedIndex >= 0 && flatListRef.current) {
      flatListRef.current.scrollToOffset({
        offset: selectedIndex * itemHeight,
        animated: false,
      });
    }
  }, [selectedIndex, itemHeight]);

  const handleMomentumScrollEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const y = e.nativeEvent.contentOffset.y;
    const index = Math.round(y / itemHeight);
    if (index >= 0 && index < items.length) {
      const chosen = items[index];
      if (chosen && chosen.value !== selectedValue) {
        onValueChange(chosen.value);
      }
    }
  };

  const handlePressItem = (index: number) => {
    if (index >= 0 && index < items.length) {
      const chosen = items[index];
      if (chosen) {
        onValueChange(chosen.value);
        flatListRef.current?.scrollToOffset({
          offset: index * itemHeight,
          animated: true,
        });
      }
    }
  };

  return (
    <View style={[styles.container, { height: itemHeight * 3, width }]}>
      {/* Center highlight row */}
      <View
        pointerEvents="none"
        style={[
          styles.highlight,
          {
            top: itemHeight,
            height: itemHeight,
          },
        ]}
      />
      <FlatList
        ref={flatListRef}
        data={items}
        keyExtractor={(item) => String(item.value)}
        showsVerticalScrollIndicator={false}
        snapToInterval={itemHeight}
        decelerationRate="fast"
        contentContainerStyle={{
          paddingVertical: itemHeight,
        }}
        onMomentumScrollEnd={handleMomentumScrollEnd}
        getItemLayout={(_, index) => ({
          length: itemHeight,
          offset: itemHeight * index,
          index,
        })}
        renderItem={({ item, index }) => {
          const isSelected = item.value === selectedValue;
          return (
            <Pressable
              onPress={() => handlePressItem(index)}
              style={[
                styles.itemRow,
                { height: itemHeight },
              ]}
            >
              <AppText
                variant={isSelected ? "title" : "caption"}
                style={[
                  styles.itemText,
                  isSelected ? styles.selectedText : styles.unselectedText,
                ]}
              >
                {item.label}
              </AppText>
            </Pressable>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "relative",
    overflow: "hidden",
  },
  highlight: {
    position: "absolute",
    left: 0,
    right: 0,
    backgroundColor: "rgba(0, 104, 95, 0.08)",
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: "rgba(0, 104, 95, 0.25)",
  },
  itemRow: {
    justifyContent: "center",
    alignItems: "center",
  },
  itemText: {
    textAlign: "center",
  },
  selectedText: {
    color: colors.primary,
    fontWeight: "700",
  },
  unselectedText: {
    color: colors.textSecondary,
    opacity: 0.6,
  },
});
